import asyncio, json
import httpx

async def main():
    # Create a new game
    async with httpx.AsyncClient(timeout=httpx.Timeout(60)) as client:
        r = await client.post("http://localhost:8000/game/new", json={"role":"villager","play_style":"balanced"})
        data = r.json()
        gid = data["game_id"]
        print(f"New game: {gid}, role: {data['human_role']}")
        
        # Collect SSE events - capture ALL events until we see last_words or game pauses
        async with client.stream("GET", f"http://localhost:8000/game/{gid}/stream") as resp:
            buffer = ""
            event_count = 0
            async for chunk in resp.aiter_bytes():
                buffer += chunk.decode("utf-8")
                while "\n\n" in buffer:
                    msg, buffer = buffer.split("\n\n", 1)
                    for line in msg.split("\n"):
                        if line.startswith("data: "):
                            data = json.loads(line[6:])
                            event_count += 1
                            phase = data.get("phase","?")
                            itype = data.get("interrupt",{}).get("type","")
                            logs = data.get("game_log",[])
                            lw = [l for l in logs if l.get("type")=="last_words"]
                            
                            print(f"\nEvent#{event_count} phase={phase} interrupt={itype} log_count={len(logs)}")
                            for l in logs:
                                print(f"  [{l.get('type')}] {l.get('message','')[:100]}")
                            
                            if lw:
                                print(f"\n!!! LAST_WORDS FOUND: {json.dumps(lw, ensure_ascii=False)}")
                                return
                            
                            if itype in ("speech","vote","witch_decision","seer_check","seer_result","werewolf_discuss"):
                                print(f"STOPPING: game waiting for human input ({itype})")
                                return
                            
                            if data.get("status") == "finished":
                                print("Game finished")
                                return
                    
                    if event_count > 20:
                        print("Too many events, stopping")
                        return

asyncio.run(main())