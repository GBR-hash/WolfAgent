import uuid, asyncio, logging, traceback, time, json
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from app.graph import build_graph
from app.config import setup_logging
import bcrypt, jwt as pyjwt
from app.database import init_db, create_user, get_user_by_username, save_game_record, get_user_records, get_record_detail

log = setup_logging("wolfagent")

import os as _os
# NLS AK/SK MUST be set in .env file, NOT in source code

JWT_SECRET = _os.getenv("JWT_SECRET", "wolfagent_dev_secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 7

def _create_token(user_id: int, username: str) -> str:
    import datetime
    payload = {"user_id": user_id, "username": username, "exp": datetime.datetime.utcnow() + datetime.timedelta(days=JWT_EXPIRY_DAYS)}
    return pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def _verify_token(token: str) -> dict | None:
    try:
        return pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None

app = FastAPI(title="WolfAgent")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
checkpointer = MemorySaver()
graph = build_graph().compile(checkpointer=checkpointer)
log.info("WolfAgent graph compiled successfully")
try:
    init_db()
    log.info("Database initialized")
except Exception:
    log.warning("Database init failed (MySQL may not be running): %s", traceback.format_exc())


class GameSession:
    def __init__(self, gid, tid):
        self.game_id = gid
        self.thread_id = tid
        self.user_id = None
        self.config = {"configurable": {"thread_id": tid}}
        self.state = None
        self.interrupt = None
        self.is_waiting = False
        self.status = "created"
        self.state_queue = asyncio.Queue()
        self._last_pushed = None

        self._speeches_history = {}
        self._votes_history = {}
        self._record_saved = False
        self._werewolf_secret_chat = []  # persists across interrupt() which loses in-place state mods
    def _push_state(self):
        try:
            snapshot = self._build_snapshot()
            skey = json.dumps(snapshot, sort_keys=True, default=str, ensure_ascii=False)
            if skey != self._last_pushed:
                self._last_pushed = skey
                lw_diag = snapshot.get('_last_words')
                if lw_diag:
                    import logging
                    logging.getLogger('wolfagent').warning('DIAG _last_words in SSE: %s', lw_diag)
                self.state_queue.put_nowait(snapshot)
        except Exception:
            pass

    def _build_snapshot(self):
        st = self.state or {}
        pl = st.get("players", {})
        return dict(
            game_id=self.game_id,
            status=self.status,
            phase=st.get("phase"),
            game_round=st.get("game_round"),
            alive_players=st.get("alive_player_ids", []),
            eliminated_players=st.get("eliminated_all", []),
            eliminated_roles={str(k): v for k, v in st.get("eliminated_roles", {}).items()},
            _night_killed_ids=st.get("_night_killed_ids", []),
            _last_words=st.get("_last_words"),
            god_announcement=st.get("god_announcement", ""),
            speeches=[{"player_id": sp.get("player_id"), "content": sp.get("content", "")} for sp in st.get("speeches", [])],
            votes={str(k): v for k, v in st.get("votes", {}).items()},
            human_role=pl.get("7", {}).get("role"),
            human_alive=pl.get("7", {}).get("is_alive", True),
            is_waiting=self.is_waiting,
            interrupt=self.interrupt,
            winner=st.get("winner"),
            game_log=st.get("game_log", []),
            speech_cursor=st.get("speech_cursor", 0),
            vote_cursor=st.get("vote_cursor", 0),
            speech_order=st.get("speech_order", []),
            vote_order=st.get("vote_order", []),
            werewolf_kill_target=st.get("werewolf_kill_target"),
            witch_heal_target=st.get("witch_heal_target"),
            witch_poison_target=st.get("witch_poison_target"),
            seer_check_target=st.get("seer_check_target"),
            seer_check_result=st.get("seer_check_result"),
            night_step=st.get("night_step", -1),
            _werewolf_secret_chat=st.get("_werewolf_secret_chat", []),
            witch_has_heal=st.get("witch_has_heal"),
            witch_has_poison=st.get("witch_has_poison"),
            players={pid: {"player_id": p.get("player_id"), "role": p.get("role"), "is_human": p.get("is_human"), "is_alive": p.get("is_alive")} for pid, p in pl.items()},
            speeches_history=self._speeches_history if self._speeches_history else st.get("speeches_history", {}),
            votes_history=self._votes_history if self._votes_history else st.get("votes_history", {}),
        )
        # Diagnostic: log history sizes for debugging
        sh_sz = len(self._speeches_history) if self._speeches_history else 0
        if sh_sz == 0:
            st_sh = st.get("speeches_history", {})
            if st_sh:
                sh_sz = len(st_sh)
        vh_sz = len(self._votes_history) if self._votes_history else 0
        if vh_sz == 0:
            st_vh = st.get("votes_history", {})
            if st_vh:
                vh_sz = len(st_vh)

sessions: dict[str, GameSession] = {}


def _sync_state(session: GameSession) -> bool:
    snap = graph.get_state(session.config)
    if snap.values:
        session.state = snap.values
        session._push_state()
    ints = getattr(snap, "interrupts", ())
    if ints:
        session.interrupt = ints[0].value
        # Persist secret_chat from interrupt to session (LangGraph interrupt()
        # does NOT checkpoint in-place state modifications like state['_werewolf_secret_chat']=...
        # We recover the value from the interrupt payload and feed it back via Command.update)
        it_val = session.interrupt or {}
        if it_val.get('type') == 'werewolf_discuss':
            sc = it_val.get('secret_chat', [])
            if sc:
                session._werewolf_secret_chat = list(sc)
        session.is_waiting = True
        session.status = "waiting"
        session._push_state()
        it = session.interrupt or {}
        log.info("[%s] INTERRUPT: type=%s, phase=%s, speech_cursor=%s, vote_cursor=%s",
                 session.game_id, it.get("type"),
                 session.state.get("phase") if session.state else "?",
                 session.state.get("speech_cursor") if session.state else "?",
                 session.state.get("vote_cursor") if session.state else "?")
        return True

    if snap.next == ():
        st = session.state or {}
        if st.get("game_over"):
            session.status = "finished"
            # Capture history data from graph state
            sh = st.get("speeches_history", {})
            vh = st.get("votes_history", {})
            if sh:
                session._speeches_history = dict(sh)
            if vh:
                session._votes_history = dict(vh)
            log.info("[%s] game over, winner=%s, speeches_history=%s rounds, votes_history=%s rounds",
                     session.game_id, st.get("winner"),
                     len(session._speeches_history), len(session._votes_history))
            session._push_state()
            if session.user_id and not session._record_saved:
                try:
                    session._record_saved = True
                    pl = st.get("players", {})
                    hr = pl.get("7", {}).get("role", "?")
                    save_game_record(
                        user_id=session.user_id,
                        game_id=session.game_id,
                        human_role=hr,
                        winner=st.get("winner"),
                        total_rounds=st.get("game_round", 0),
                        is_alive=pl.get("7", {}).get("is_alive", False),
                        players=pl,
                        game_log=st.get("game_log", []),
                        speeches=st.get("speeches", []),
                        votes=st.get("votes", {}),
                    )
                except Exception:
                    log.error("[%s] Failed to archive game record: %s", session.game_id, traceback.format_exc())
        else:
            log.warning("[%s] graph ended but game_over not set, force check", session.game_id)
            players = st.get("players", {})
            wolves = sum(1 for p in players.values() if p.get("is_alive") and p.get("role") == "werewolf")
            others = sum(1 for p in players.values() if p.get("is_alive") and p.get("role") != "werewolf")
            if wolves == 0:
                st["game_over"] = True; st["winner"] = "villager"
            elif wolves >= others:
                st["game_over"] = True; st["winner"] = "werewolf"
            else:
                st["game_over"] = True; st["winner"] = "villager"
            session.state = st
            session.status = "finished"
            session._push_state()
            log.warning("[%s] fallback winner=%s", session.game_id, st["winner"])
            if session.user_id and not session._record_saved:
                try:
                    session._record_saved = True
                    pl = st.get("players", {})
                    hr = pl.get("7", {}).get("role", "?")
                    save_game_record(
                        user_id=session.user_id,
                        game_id=session.game_id,
                        human_role=hr,
                        winner=st.get("winner"),
                        total_rounds=st.get("game_round", 0),
                        is_alive=pl.get("7", {}).get("is_alive", False),
                        players=pl,
                        game_log=st.get("game_log", []),
                        speeches=st.get("speeches", []),
                        votes=st.get("votes", {}),
                    )
                except Exception:
                    log.error("[%s] Failed to archive game record: %s", session.game_id, traceback.format_exc())
        return False
    return False


async def _advance(session: GameSession):
    if _sync_state(session):
        return
    try:
        t0 = time.time()
        log.debug("[%s] _advance: calling graph.astream...", session.game_id)
        event_count = 0
        async for event in graph.astream(None, session.config, stream_mode="updates"):
            event_count += 1
            if isinstance(event, dict):
                for nm, up in event.items():
                    if up and isinstance(up, dict):
                        session.state = up
                        if up.get("speeches_history"):
                            session._speeches_history = dict(up["speeches_history"])
                        if up.get("votes_history"):
                            session._votes_history = dict(up["votes_history"])
                        # Refresh with full graph state before pushing snapshot
                        snap = graph.get_state(session.config)
                        if snap.values:
                            session.state = snap.values
                        session._push_state()
                        # Spectator delay: give frontend time to render each phase
                        human_dead = not (session.state or {}).get("players", {}).get("7", {}).get("is_alive", True)
                        if human_dead:
                            await asyncio.sleep(1.5)
                        log.info("[%s] NODE #%d: %s -> phase=%s, cursor(s=%s,v=%s)",
                                 session.game_id, event_count, nm, up.get("phase", "?"),
                                 up.get("speech_cursor", "?"), up.get("vote_cursor", "?"))
            elif isinstance(event, tuple) and len(event) == 2:
                nm, up = event
                if up and isinstance(up, dict):
                    session.state = up
                    if up.get("speeches_history"):
                        session._speeches_history = dict(up["speeches_history"])
                    if up.get("votes_history"):
                        session._votes_history = dict(up["votes_history"])
                    # Refresh with full graph state before pushing snapshot
                    snap = graph.get_state(session.config)
                    if snap.values:
                        session.state = snap.values
                    session._push_state()
                    # Spectator delay: give frontend time to render each phase
                    human_dead = not (session.state or {}).get("players", {}).get("7", {}).get("is_alive", True)
                    if human_dead:
                        await asyncio.sleep(1.5)
                    log.info("[%s] NODE #%d: %s -> phase=%s, cursor(s=%s,v=%s)",
                             session.game_id, event_count, nm, up.get("phase", "?"),
                             up.get("speech_cursor", "?"), up.get("vote_cursor", "?"))
            else:
                log.debug("[%s] unexpected event format: %s", session.game_id, type(event).__name__)

            if _sync_state(session):
                elapsed = time.time() - t0
                log.info("[%s] _advance: interrupted after %d events (%.1fs)",
                         session.game_id, event_count, elapsed)
                return
        elapsed = time.time() - t0
        log.info("[%s] _advance: stream ended after %d events (%.1fs)",
                 session.game_id, event_count, elapsed)
    except Exception:
        log.error("[%s] _advance crashed:\n%s", session.game_id, traceback.format_exc())
        raise
    _sync_state(session)


async def _auto(session: GameSession):
    try:
        while session.status not in ("waiting", "finished", "error"):
            await _advance(session)
    except Exception as e:
        log.error("[%s] _auto crashed: %s", session.game_id, traceback.format_exc())
        session.status = "error"
        session.interrupt = {"type": "error", "message": str(e)}


class ActionRequest(BaseModel):
    action: str


class AuthRequest(BaseModel):
    username: str
    password: str

class NewGameRequest(BaseModel):
    role: str = "random"
    play_style: str = "balanced"
    token: str | None = None

VALID_ROLES = {"random", "werewolf", "witch", "seer", "villager"}

@app.post("/auth/register")
async def auth_register(req: AuthRequest):
    if not req.username or not req.password:
        raise HTTPException(400, "Username and password required")
    if len(req.username) < 2 or len(req.username) > 20:
        raise HTTPException(400, "Username must be 2-20 characters")
    pwd_hash = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
    user_id = create_user(req.username, pwd_hash)
    if user_id is None:
        raise HTTPException(409, "Username already exists")
    token = _create_token(user_id, req.username)
    return {"token": token, "user_id": user_id, "username": req.username}

@app.post("/auth/login")
async def auth_login(req: AuthRequest):
    user = get_user_by_username(req.username)
    if not user:
        raise HTTPException(401, "Invalid username or password")
    if not bcrypt.checkpw(req.password.encode(), user["password_hash"].encode()):
        raise HTTPException(401, "Invalid username or password")
    token = _create_token(user["id"], user["username"])
    return {"token": token, "user_id": user["id"], "username": user["username"]}

@app.get("/auth/me")
async def auth_me(authorization: str = Header(default="")):
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else ""
    if not token:
        raise HTTPException(401, "No token provided")
    payload = _verify_token(token)
    if not payload:
        raise HTTPException(401, "Invalid or expired token")
    return {"user_id": payload["user_id"], "username": payload["username"]}

@app.get("/records")
async def list_records(authorization: str = Header(default="")):
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else ""
    if not token:
        raise HTTPException(401, "No token provided")
    payload = _verify_token(token)
    if not payload:
        raise HTTPException(401, "Invalid or expired token")
    records = get_user_records(payload["user_id"])
    return {"records": records}

@app.get("/records/{game_id}")
async def record_detail(game_id: str, authorization: str = Header(default="")):
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else ""
    if not token:
        raise HTTPException(401, "No token provided")
    payload = _verify_token(token)
    if not payload:
        raise HTTPException(401, "Invalid or expired token")
    record = get_record_detail(payload["user_id"], game_id)
    if not record:
        raise HTTPException(404, "Record not found")
    return record


@app.post("/game/new")
async def new_game(req: NewGameRequest = NewGameRequest()):
    gid = str(uuid.uuid4())[:8]
    chosen_role = req.role if req.role in VALID_ROLES else "random"
    log.info("[%s] new game, chosen_role=%s", gid, chosen_role)
    s = GameSession(gid, gid)
    sessions[gid] = s
    if req.token:
        payload = _verify_token(req.token)
        if payload:
            s.user_id = payload["user_id"]
            log.info("[%s] game associated with user %s", gid, payload["username"])
    try:
        init_state = {"phase": "init", "play_style": req.play_style}
        if chosen_role != "random":
            init_state["human_role"] = chosen_role
        async for ev in graph.astream(init_state, s.config, stream_mode="updates"):
            if isinstance(ev, dict):
                for nm, up in ev.items():
                    if up and isinstance(up, dict):
                        s.state = up
                        log.info("[%s] NODE COMPLETE: %s", gid, nm)
            elif isinstance(ev, tuple) and len(ev) == 2:
                nm, up = ev
                if up and isinstance(up, dict):
                    s.state = up
                    log.info("[%s] NODE COMPLETE: %s", gid, nm)
            break
    except Exception as e:
        log.error("[%s] init failed: %s", gid, traceback.format_exc())
        raise HTTPException(500, str(e))
    _sync_state(s)
    st = s.state or {}
    pl = st.get("players", {})
    hr = pl.get("7", {}).get("role", "?")
    rc = {"werewolf": "werewolf", "witch": "witch", "seer": "seer", "villager": "villager"}
    s.status = "running"
    asyncio.create_task(_auto(s))
    log.info("[%s] game started, human role=%s", gid, rc.get(hr, hr))
    return {"game_id": gid, "human_role": rc.get(hr, hr), "message": f"Game started! Role: {rc.get(hr, hr)}"}


@app.get("/game/{gid}")
async def game_status(gid: str):
    s = sessions.get(gid)
    if not s:
        raise HTTPException(404, "Not found")
    st = s.state or {}
    pl = st.get("players", {})
    return dict(
        game_id=gid,
        status=s.status,
        phase=st.get("phase"),
        game_round=st.get("game_round"),
        alive_players=st.get("alive_player_ids", []),
        eliminated_players=st.get("eliminated_all", []),
        eliminated_roles=st.get("eliminated_roles", {}),
        god_announcement=st.get("god_announcement", ""),
        speeches=st.get("speeches", []),
        votes=st.get("votes", {}),
        human_role=pl.get("7", {}).get("role"),
        is_waiting=s.is_waiting,
        interrupt_type=s.interrupt.get("type") if s.interrupt else None,
        interrupt_prompt=s.interrupt.get("prompt") if s.interrupt else None,
        winner=st.get("winner"),
        game_log=st.get("game_log", []),
        speech_cursor=st.get("speech_cursor", 0),
        vote_cursor=st.get("vote_cursor", 0),
        speech_order=st.get("speech_order", []),
        vote_order=st.get("vote_order", []),
    )


@app.post("/game/{gid}/action")
async def action(gid: str, req: ActionRequest):
    s = sessions.get(gid)
    if not s:
        raise HTTPException(404, "Not found")
    if not s.is_waiting:
        raise HTTPException(400, "Not waiting")

    it = s.interrupt or {}
    log.info("[%s] ACTION: type=%s, input=%.60s", gid, it.get("type"), req.action)

    s.is_waiting = False
    s.interrupt = None
    s.status = "running"
    try:
        t0 = time.time()
        event_count = 0
        # Persist secret_chat to graph state before resume, because
        # interrupt() does NOT checkpoint in-place state modifications.
        # Using graph.update_state() instead of Command.update to avoid
        # InvalidUpdateError (same-step double-write conflict).
        if s._werewolf_secret_chat:
            graph.update_state(s.config, {'_werewolf_secret_chat': s._werewolf_secret_chat})
        async for ev in graph.astream(Command(resume=req.action), s.config, stream_mode='updates'):
            event_count += 1
            if isinstance(ev, dict):
                for nm, up in ev.items():
                    if up and isinstance(up, dict):
                        s.state = up
                        # Update session history from node return
                        if up.get("speeches_history"):
                            s._speeches_history = dict(up["speeches_history"])
                        if up.get("votes_history"):
                            s._votes_history = dict(up["votes_history"])
                        # Refresh with full graph state before pushing snapshot
                        snap = graph.get_state(s.config)
                        if snap.values:
                            s.state = snap.values
                        s._push_state()
                        # Spectator delay for eliminated human
                        human_dead = not (s.state or {}).get("players", {}).get("7", {}).get("is_alive", True)
                        if human_dead:
                            await asyncio.sleep(1.5)
                        log.info("[%s] RESUME #%d: %s -> phase=%s, cursor(s=%s,v=%s)",
                                 gid, event_count, nm, up.get("phase", "?"),
                                 up.get("speech_cursor", "?"), up.get("vote_cursor", "?"))
            elif isinstance(ev, tuple) and len(ev) == 2:
                nm, up = ev
                if up and isinstance(up, dict):
                    s.state = up
                    if up.get("speeches_history"):
                        s._speeches_history = dict(up["speeches_history"])
                    if up.get("votes_history"):
                        s._votes_history = dict(up["votes_history"])
                    # Refresh with full graph state before pushing snapshot
                    snap = graph.get_state(s.config)
                    if snap.values:
                        s.state = snap.values
                    s._push_state()
                    # Spectator delay for eliminated human
                    human_dead = not (s.state or {}).get("players", {}).get("7", {}).get("is_alive", True)
                    if human_dead:
                        await asyncio.sleep(1.5)
                    log.info("[%s] RESUME #%d: %s -> phase=%s, cursor(s=%s,v=%s)",
                             gid, event_count, nm, up.get("phase", "?"),
                             up.get("speech_cursor", "?"), up.get("vote_cursor", "?"))

            if _sync_state(s):
                elapsed = time.time() - t0
                log.info("[%s] RESUME: next interrupt after %d events (%.1fs), type=%s",
                         gid, event_count, elapsed, s.interrupt.get("type") if s.interrupt else "?")
                return {"success": True, "message": "Waiting for next input"}
        elapsed = time.time() - t0
        log.info("[%s] RESUME: stream ended after %d events (%.1fs)", gid, event_count, elapsed)
    except Exception as e:
        log.error("[%s] action crashed:\n%s", gid, traceback.format_exc())
        raise HTTPException(500, str(e))
    if _sync_state(s):
        log.info("[%s] next interrupt: %s", gid, s.interrupt.get("type") if s.interrupt else "?")
        return {"success": True, "message": "Waiting for next input"}
    log.info("[%s] no next interrupt, status=%s", gid, s.status)
    return {"success": True, "message": "OK"}


@app.get("/game/{gid}/stream")
async def game_stream(gid: str):
    s = sessions.get(gid)
    if not s:
        raise HTTPException(404, "Not found")

    async def event_generator():
        snapshot = s._build_snapshot()
        yield {"event": "state", "data": json.dumps(snapshot, default=str, ensure_ascii=False)}

        while s.status not in ("finished", "error"):
            try:
                new_state = await asyncio.wait_for(s.state_queue.get(), timeout=30.0)
                yield {"event": "state", "data": json.dumps(new_state, default=str, ensure_ascii=False)}
            except asyncio.TimeoutError:
                yield {"event": "heartbeat", "data": ""}
                if s.status in ("finished", "error"):
                    break

        # Drain any remaining states from the queue before sending final
        drained = 0
        while not s.state_queue.empty():
            try:
                leftover = s.state_queue.get_nowait()
                yield {"event": "state", "data": json.dumps(leftover, default=str, ensure_ascii=False)}
                drained += 1
            except Exception:
                break
        if drained > 0:
            log.debug("[%s] SSE drained %d leftover states from queue", s.game_id, drained)

        final = s._build_snapshot()
        yield {"event": "state", "data": json.dumps(final, default=str, ensure_ascii=False)}

    return EventSourceResponse(event_generator())


@app.get("/game/{gid}/debug")
async def debug(gid: str):
    s = sessions.get(gid)
    if not s:
        raise HTTPException(404, "Not found")
    return dict(
        game_id=gid,
        status=s.status,
        is_waiting=s.is_waiting,
        interrupt=s.interrupt,
        state=s.state,
    )


@app.get("/speak")
async def speak(text: str):
    import asyncio as _asyncio
    from nls import NlsSpeechSynthesizer, token
    from starlette.responses import StreamingResponse

    tok = token.getToken(
        _os.environ["NLS_AK_ID"],
        _os.environ["NLS_AK_SECRET"],
    )

    q: _asyncio.Queue = _asyncio.Queue()
    loop = _asyncio.get_running_loop()

    def on_data(data, raw=None):
        loop.call_soon_threadsafe(q.put_nowait, ("data", data))

    def on_error(msg, raw=None):
        loop.call_soon_threadsafe(q.put_nowait, ("error", str(msg)))

    def on_completed(msg, raw=None):
        loop.call_soon_threadsafe(q.put_nowait, ("done", None))

    tts = NlsSpeechSynthesizer(
        on_data=on_data,
        on_error=on_error,
        on_completed=on_completed,
        token=tok,
        appkey="1qLRqf02vTCzt90z",
    )

    def _run_tts():
        tts.start(
            text=text,
            voice="laotie",
            aformat="mp3",
            volume=50,
            speech_rate=204,
            pitch_rate=4,
            wait_complete=True,
            start_timeout=10,
            completed_timeout=30,
        )

    _asyncio.get_running_loop().run_in_executor(None, _run_tts)

    async def generate():
        while True:
            kind, payload = await q.get()
            if kind == "data":
                yield payload
            elif kind == "done":
                return
            elif kind == "error":
                return

    return StreamingResponse(generate(), media_type="audio/mpeg",
                             headers={"X-Accel-Buffering": "no"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

