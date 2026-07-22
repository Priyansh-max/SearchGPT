"""
Tier-aware concurrency lanes + memory guard (Problem 1).

Demo and signed-in traffic draw from SEPARATE slot pools, so a flood of demo scrapes can
never starve signed-in users (the core fairness guarantee). When a lane is full we fail fast
with BusyError (the caller turns this into a graceful "we're busy, try again / sign in to skip
the queue" response) instead of crashing or blocking forever. A memory guard refuses new work
when free memory drops below a threshold, so the box degrades gracefully instead of OOMing.

The class is pure asyncio state (no browser), so it is fully unit-testable offline.

Deferred (documented): letting demo BORROW idle signed-in slots with preemption. True
preemption is hard to do safely with cooperative async; separate fail-fast lanes already give
the isolation guarantee. Revisit if utilization needs it.
"""
import asyncio
import contextlib
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class BusyError(Exception):
    """No capacity available right now — caller should return a graceful 'busy' response."""


class ConcurrencyManager:
    def __init__(
        self,
        signedin_slots: int = 2,
        demo_slots: int = 1,
        *,
        memory_guard_mb: int = 0,
        mem_free_fn: Optional[Callable[[], Optional[float]]] = None,
    ):
        self._cap = {"signedin": max(0, signedin_slots), "demo": max(0, demo_slots)}
        self._in_use = {"signedin": 0, "demo": 0}
        self._lock = asyncio.Lock()
        self.memory_guard_mb = memory_guard_mb
        self._mem_free_fn = mem_free_fn

    @staticmethod
    def _lane(tier: str) -> str:
        return "signedin" if tier == "signedin" else "demo"

    async def _acquire(self, lane: str) -> None:
        async with self._lock:
            if self.memory_guard_mb and self._mem_free_fn is not None:
                free = self._mem_free_fn()
                if free is not None and free < self.memory_guard_mb:
                    raise BusyError(f"low memory: {free:.0f}MB free < {self.memory_guard_mb}MB")
            if self._cap[lane] <= 0:
                raise BusyError(f"no capacity configured for '{lane}' lane")
            if self._in_use[lane] >= self._cap[lane]:
                raise BusyError(f"'{lane}' lane busy ({self._in_use[lane]}/{self._cap[lane]})")
            self._in_use[lane] += 1

    async def _release(self, lane: str) -> None:
        async with self._lock:
            self._in_use[lane] = max(0, self._in_use[lane] - 1)

    @contextlib.asynccontextmanager
    async def slot(self, tier: str = "demo"):
        """Acquire a slot for the given tier ('signedin'|'demo'); BusyError if the lane is full."""
        lane = self._lane(tier)
        await self._acquire(lane)
        try:
            yield
        finally:
            await self._release(lane)

    def stats(self) -> dict:
        return {
            "signedin": {"in_use": self._in_use["signedin"], "cap": self._cap["signedin"]},
            "demo": {"in_use": self._in_use["demo"], "cap": self._cap["demo"]},
        }


def default_mem_free_fn() -> Optional[Callable[[], Optional[float]]]:
    """Return a callable giving free MB via psutil, or None if psutil isn't installed."""
    try:
        import psutil  # optional

        def _free_mb() -> Optional[float]:
            return psutil.virtual_memory().available / (1024 * 1024)

        return _free_mb
    except Exception:
        logger.info("psutil not available; memory guard disabled")
        return None


# Module-level manager configured from settings on first use.
_manager: Optional[ConcurrencyManager] = None


def get_manager() -> ConcurrencyManager:
    global _manager
    if _manager is None:
        try:
            from config import settings
            _manager = ConcurrencyManager(
                signedin_slots=settings.SIGNEDIN_SLOTS,
                demo_slots=settings.DEMO_SLOTS,
                memory_guard_mb=settings.MEMORY_GUARD_MB,
                mem_free_fn=default_mem_free_fn(),
            )
        except Exception:
            _manager = ConcurrencyManager()
    return _manager
