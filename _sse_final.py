import asyncio, json, sys
import httpx

async def main():
    async with httpx.AsyncClient(timeout=httpx.Timeout(90)) as client:
        # Create game with human as villager
        r = await client.post("http://localhost:8000/game/new", json={"role":"villager","play_style":"balanced"})
        gid = r.json()["game_id"]
        print(f"Game: {gid}")
        
        seen_last_words = False
        event_count = 0
        
        async with client.stream("GET", f"http://localhost:8000/game/{gid}/stream") as resp:
            buffer = ""
            async for chunk in resp.aiter_bytes():
                buffer += chunk.decode("utf-8")
                while "\n\n" in buffer:
                    msg, buffer = buffer.split("\n\n", 1)
                    for line in msg.split("\n"):
                        if not line.startswith("data: "):
                            continue
                        event_count += 1
                        data = json.loads(line[6:])
                        logs = data.get("game_log", [])
                        itype = (data.get("interrupt") or {}).get("type", "")
                        
                        # Check for last_words
                        for l in logs:
                            if l.get("type") == "last_words":
                                seen_last_words = True
                                print(f"!!! EVENT#{event_count} HAS LAST_WORDS: {json.dumps(l, ensure_ascii=False)}")
                        
                        if event_count <= 3 or seen_last_words:
                            print(f"  Event#{event_count} phase={data.get('phase')} interrupt={itype} log_count={len(logs)} log_types={[l['type'] for l in logs]}")
                        
                        # Auto-respond to human actions
                        if itype == "speech":
                            await client.post(f"http://localhost:8000/game/{gid}/action", json={"action": "我是村民，过"})
                        elif itype == "vote":
                            await client.post(f"http://localhost:8000/game/{gid}/action", json={"action": "0"})
                        elif itype in ("witch_decision", "seer_check", "seer_result", "werewolf_discuss"):
                            pass  # human is villager, shouldn't happen
                        
                        if seen_last_words:
                            break
                    
                    if seen_last_words or event_count > 15:
                        break
        
        if seen_last_words:
            print("\nSUCCESS: Last words found in SSE stream!")
        else:
            print(f"\nFAILED: No last_words in {event_count} SSE events")

asyncio.run(main())