import asyncio, json, sys
import httpx

async def main():
    gid = "5997ea3b"
    
    # Collect SSE events
    events = []
    
    async with httpx.AsyncClient(timeout=httpx.Timeout(120)) as client:
        async with client.stream("GET", f"http://localhost:8000/game/{gid}/stream") as response:
            buffer = ""
            async for chunk in response.aiter_bytes():
                buffer += chunk.decode("utf-8")
                while "\n\n" in buffer:
                    msg, buffer = buffer.split("\n\n", 1)
                    for line in msg.split("\n"):
                        if line.startswith("data: "):
                            data = json.loads(line[6:])
                            phase = data.get("phase", "?")
                            gtype = data.get("interrupt", {}).get("type", "")
                            game_log = data.get("game_log", [])
                            
                            # Check for last_words in game_log
                            lw = [l for l in game_log if l.get("type") == "last_words"]
                            if lw:
                                print(f"!!! LAST_WORDS FOUND: {lw}")
                            
                            events.append({
                                "phase": phase,
                                "interrupt_type": gtype,
                                "log_count": len(game_log),
                                "log_types": [l.get("type") for l in game_log[-3:]],
                                "has_last_words": bool(lw),
                            })
                            
                            # Auto-respond to seer check
                            if gtype == "seer_check":
                                print("SEER: auto-checking player 1")
                                await asyncio.sleep(0.5)
                                r = await client.post(f"http://localhost:8000/game/{gid}/action", json={"action": "1"})
                            
                            # Auto-respond to speech
                            if gtype == "speech":
                                print("SPEECH: auto-speech")
                                await asyncio.sleep(0.3)
                                r = await client.post(f"http://localhost:8000/game/{gid}/action", json={"action": "我是预言家，昨晚查了1号是好人"})
                            
                            # Auto-respond to vote
                            if gtype == "vote":
                                print("VOTE: auto-vote 0 (skip)")
                                await asyncio.sleep(0.3)
                                r = await client.post(f"http://localhost:8000/game/{gid}/action", json={"action": "0"})
                            
                            # Stop if game finished
                            if data.get("status") == "finished":
                                print("GAME FINISHED")
                                break
                    if data.get("status") == "finished":
                        break
            # Print summary
            print("\n=== EVENT SUMMARY ===")
            for i, e in enumerate(events):
                print(f"[{i}] phase={e['phase']} interrupt={e['interrupt_type']} log_count={e['log_count']} log_types={e['log_types']} has_last_words={e['has_last_words']}")
            
            # Final check
            last_words_any = any(e["has_last_words"] for e in events)
            print(f"\nAny last_words found: {last_words_any}")

asyncio.run(main())