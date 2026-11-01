import asyncio
import pytest

from app.core.retry import retry_async


@pytest.mark.asyncio
async def test_agent_timeout():
    async def slow_agent():
        await asyncio.sleep(2)
        return "success"

    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(
            slow_agent(),
            timeout=0.1,
        )


@pytest.mark.asyncio
async def test_retry_after_transient_failure():
    attempts = 0

    class TemporaryError(Exception):
        status_code = 503

    async def flaky_operation():
        nonlocal attempts
        attempts += 1

        if attempts < 3:
            raise TemporaryError("Temporary provider failure")

        return "success"

    result = await retry_async(
        flaky_operation,
        max_attempts=3,
        base_delay=0.01,
    )

    assert result == "success"
    assert attempts == 3