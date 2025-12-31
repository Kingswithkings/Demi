import asyncio
from typing import Any

def run_async(coro):
    """
    Safely run an async coroutine from Streamlit.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # If Streamlit (or environment) already has a running loop, create a new one.
        new_loop = asyncio.new_event_loop()
        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()
    else:
        return asyncio.run(coro)
