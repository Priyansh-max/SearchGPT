"""
Tests for tier-aware concurrency lanes + memory guard (Problem 1). Pure asyncio, offline.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.concurrency import ConcurrencyManager, BusyError  # noqa: E402


def run(coro):
    return asyncio.run(coro)


def test_acquire_within_capacity():
    async def scenario():
        cm = ConcurrencyManager(signedin_slots=2, demo_slots=1)
        async with cm.slot("signedin"):
            assert cm.stats()["signedin"]["in_use"] == 1
        assert cm.stats()["signedin"]["in_use"] == 0
    run(scenario())


def test_demo_cannot_starve_signedin():
    """The core guarantee: demo lane full -> signed-in lane still available."""
    async def scenario():
        cm = ConcurrencyManager(signedin_slots=1, demo_slots=1)
        async with cm.slot("demo"):                 # demo now full
            try:
                async with cm.slot("demo"):
                    assert False, "expected BusyError on second demo"
            except BusyError:
                pass
            # signed-in is a separate pool and remains free
            async with cm.slot("signedin"):
                assert cm.stats()["signedin"]["in_use"] == 1
    run(scenario())


def test_lane_full_raises_busy():
    async def scenario():
        cm = ConcurrencyManager(signedin_slots=1, demo_slots=1)
        async with cm.slot("signedin"):
            try:
                async with cm.slot("signedin"):
                    assert False
            except BusyError:
                pass
    run(scenario())


def test_release_frees_slot():
    async def scenario():
        cm = ConcurrencyManager(signedin_slots=1, demo_slots=1)
        async with cm.slot("demo"):
            pass
        async with cm.slot("demo"):                 # reusable after release
            assert cm.stats()["demo"]["in_use"] == 1
    run(scenario())


def test_zero_capacity_lane_busy():
    async def scenario():
        cm = ConcurrencyManager(signedin_slots=0, demo_slots=1)
        try:
            async with cm.slot("signedin"):
                assert False
        except BusyError:
            pass
    run(scenario())


def test_memory_guard_blocks_when_low():
    async def scenario():
        cm = ConcurrencyManager(signedin_slots=2, demo_slots=2,
                                memory_guard_mb=200, mem_free_fn=lambda: 50.0)
        try:
            async with cm.slot("demo"):
                assert False, "expected BusyError from memory guard"
        except BusyError as e:
            assert "memory" in str(e).lower()
    run(scenario())


def test_memory_guard_allows_when_ample():
    async def scenario():
        cm = ConcurrencyManager(signedin_slots=2, demo_slots=2,
                                memory_guard_mb=200, mem_free_fn=lambda: 4000.0)
        async with cm.slot("demo"):
            assert cm.stats()["demo"]["in_use"] == 1
    run(scenario())
