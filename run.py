"""
Entry point for running the procurement server locally.
Sets WindowsSelectorEventLoopPolicy before uvicorn creates its event loop,
which is required for psycopg3 async on Windows (Python < 3.14).
"""
import asyncio
import sys

if sys.platform == "win32" and sys.version_info < (3, 14):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    reload = "--reload" in sys.argv
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=reload)
