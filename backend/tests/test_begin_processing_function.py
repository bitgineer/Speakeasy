"""Tests for core.processing.begin_processing and cancel_processing."""

import asyncio

import pytest

from speakeasy.core import processing
from speakeasy.core.processing import ProcessingRun, begin_processing, cancel_processing


def test_begin_processing_returns_the_module_run():
    assert begin_processing() is processing._active_run


def test_begin_processing_bumps_the_generation():
    before = processing._active_run.generation

    run = begin_processing()

    assert run.generation == before + 1


async def test_begin_processing_cancels_an_in_flight_task():
    run = begin_processing()
    started = asyncio.Event()

    async def work():
        started.set()
        await asyncio.sleep(30)

    task = asyncio.create_task(work())
    await started.wait()
    run.task = task

    begin_processing()

    with pytest.raises(asyncio.CancelledError):
        await task
    assert run.task is None


async def test_cancel_processing_bumps_the_generation_and_cancels():
    run = begin_processing()
    before = run.generation
    started = asyncio.Event()

    async def work():
        started.set()
        await asyncio.sleep(30)

    task = asyncio.create_task(work())
    await started.wait()
    run.task = task

    cancel_processing()

    assert run.generation == before + 1
    with pytest.raises(asyncio.CancelledError):
        await task
    assert run.task is None


def test_supersede_is_idempotent():
    run = ProcessingRun()

    run.supersede()
    run.supersede()

    assert run.generation == 2
    assert run.task is None


def test_supersede_handles_a_finished_task_without_error():
    run = ProcessingRun()

    async def work():
        return "done"

    async def finish():
        run.task = asyncio.create_task(work())
        await run.task

    asyncio.run(finish())
    run.supersede()

    assert run.generation == 1
    assert run.task is None
