import asyncio
import logging
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def retry_async(
    operation: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 8.0,
) -> T:
    for attempt in range(1, max_attempts + 1):
        try:
            return await operation()

        except asyncio.CancelledError:
            raise

        except Exception as exc:
            if not is_retryable(exc) or attempt == max_attempts:
                raise

            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            delay += random.uniform(0, delay * 0.2)

            logger.warning(
                "Transient failure. Attempt %s/%s. Retrying in %.2fs. Error: %s",
                attempt,
                max_attempts,
                delay,
                type(exc).__name__,
            )

            await asyncio.sleep(delay)

    raise RuntimeError("Retry attempts exhausted")


def is_retryable(exc: Exception) -> bool:
    # Keep this conservative. Extend it for your provider's SDK
    # after confirming its actual exception types.
    status_code = (
        getattr(exc, "status_code", None)
        or getattr(getattr(exc, "response", None), "status_code", None)
    )

    if status_code == 429 or (
        isinstance(status_code, int) and 500 <= status_code <= 599
    ):
        return True

    return isinstance(
        exc,
        (
            TimeoutError,
            ConnectionError,
            OSError,
        ),
    )