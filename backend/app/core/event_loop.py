"""
Bridge from background threads to the application's asyncio event loop.

The alert scheduler runs in an APScheduler worker thread, which has no event
loop, so `asyncio.create_task(...)` there fails with "no running event loop".
Instead, the FastAPI lifespan registers the server's loop at startup and
threads submit coroutines to it with `run_coroutine_from_thread`, which waits
(bounded) for the result so nothing is left running after shutdown.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import threading
from typing import Any, Coroutine

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_main_loop: asyncio.AbstractEventLoop | None = None


def set_main_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _main_loop
    with _lock:
        _main_loop = loop


def clear_main_loop() -> None:
    global _main_loop
    with _lock:
        _main_loop = None


def get_main_loop() -> asyncio.AbstractEventLoop | None:
    with _lock:
        return _main_loop


def run_coroutine_from_thread(coro: Coroutine[Any, Any, Any], timeout: float = 5.0) -> bool:
    """Run `coro` on the main event loop from a worker thread.

    Returns True if it completed, False if it could not run, failed or timed
    out (the failure is logged; nothing is raised to the caller).
    """
    loop = get_main_loop()
    if loop is None or loop.is_closed() or not loop.is_running():
        coro.close()  # avoid "coroutine was never awaited" warnings
        logger.warning("No running application event loop; async notification skipped")
        return False

    try:
        running = asyncio.get_running_loop()
    except RuntimeError:
        running = None
    if running is loop:
        # Called from the loop thread itself: blocking here would deadlock.
        loop.create_task(coro)
        return True

    future = asyncio.run_coroutine_threadsafe(coro, loop)
    try:
        future.result(timeout=timeout)
        return True
    except concurrent.futures.TimeoutError:
        future.cancel()
        logger.warning("Async notification timed out after %.1fs and was cancelled", timeout)
    except Exception as exc:
        logger.warning("Async notification failed: %s", type(exc).__name__)
    return False
