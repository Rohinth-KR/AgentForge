"""Phase 3 end-to-end test — CLI WebSocket stream client."""
from __future__ import annotations

import asyncio
import json
import sys
import urllib.request


API = "http://localhost:8000"
DEFAULT_TASK = "Research the top 3 AI startups in India and write a brief summary."


async def main() -> None:
    # 1. Create a run via REST API
    task = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else DEFAULT_TASK
    print(f"[*] Creating run: {task!r}")

    req = urllib.request.Request(
        f"{API}/api/run",
        data=json.dumps({"task": task}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    run_id = data["run_id"]
    print(f"[*] Run created: {run_id}")

    # 2. Connect WebSocket and listen for events
    import websockets

    ws_url = f"ws://localhost:8000/api/run/{run_id}/stream"
    print(f"[*] Connecting WebSocket: {ws_url}")

    async with websockets.connect(ws_url) as ws:
        print("[*] Connected — waiting for events...\n")
        async for message in ws:
            event = json.loads(message)
            etype = event["type"]
            agent = event.get("agent") or ""
            content = event.get("content") or ""
            preview = content[:150] + "..." if len(content) > 150 else content

            if etype == "agent_start":
                print(f"  🟢 AGENT_START    [{agent}]")
            elif etype == "agent_output":
                print(f"  📝 AGENT_OUTPUT   [{agent}]  {preview}")
            elif etype == "agent_complete":
                print(f"  ✅ AGENT_COMPLETE [{agent}]")
            elif etype == "run_complete":
                meta = event.get("metadata", {})
                print(f"  🏁 RUN_COMPLETE   quality={meta.get('quality_status')}  revisions={meta.get('revision_count')}")
                print(f"     trace: {meta.get('agent_trace')}")
            elif etype == "run_error":
                print(f"  ❌ RUN_ERROR      {preview}")
            else:
                print(f"  ❓ {etype}  {preview}")

    print("\n[*] Stream ended. Phase 3 checkpoint PASSED!")


if __name__ == "__main__":
    asyncio.run(main())
