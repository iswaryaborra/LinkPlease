from dataclasses import dataclass


@dataclass
class RetryPolicy:
    """
    Configuration for retrying temporary API failures.
    """

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0

    def get_delay(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay.

        Attempt 1 -> 1 second
        Attempt 2 -> 2 seconds
        Attempt 3 -> 4 seconds

        The delay is capped by max_delay.
        """

        delay = self.base_delay * (2 ** (attempt - 1))

        return min(delay, self.max_delay)


def should_retry(
    *,
    status_code: int,
    attempt: int,
    max_attempts: int = 3,
) -> bool:
    """
    Determine whether an API request should be retried.

    400 -> never retry
    429 -> retry
    500 -> retry
    Other responses -> don't retry
    """

    if attempt >= max_attempts:
        return False

    if status_code == 400:
        return False

    if status_code in {429, 500}:
        return True

    return False