import pytest

from app.core.retry import retry_async


class TemporaryError(Exception):
    status_code = 503


@pytest.mark.asyncio
async def test_retries_then_succeeds():
    attempts = 0

    async def flaky_operation():
        nonlocal attempts
        attempts += 1

        if attempts < 3:
            raise TemporaryError("Service unavailable")

        return "success"

    result = await retry_async(
        flaky_operation,
        max_attempts=3,
        base_delay=0.01,
    )

    assert result == "success"
    assert attempts == 3


@pytest.mark.asyncio
async def test_does_not_retry_permanent_error():
    attempts = 0

    async def failing_operation():
        nonlocal attempts
        attempts += 1
        raise ValueError("Invalid input")

    with pytest.raises(ValueError):
        await retry_async(failing_operation, max_attempts=3)

    assert attempts == 1