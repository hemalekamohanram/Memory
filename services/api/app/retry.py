import random
import time
from collections.abc import Callable

from sqlalchemy.exc import DBAPIError


def is_serialization_failure(exc: BaseException) -> bool:
    code = getattr(getattr(exc, "orig", None), "sqlstate", None)
    return code == "40001" or "restart transaction" in str(exc).lower()


def with_serialization_retry[T](operation: Callable[[], T], attempts: int = 4,
                                base_delay: float = 0.025) -> T:
    for attempt in range(attempts):
        try:
            return operation()
        except DBAPIError as exc:
            if not is_serialization_failure(exc) or attempt == attempts - 1:
                raise
            time.sleep(base_delay * (2 ** attempt) + random.uniform(0, base_delay))
    raise RuntimeError("unreachable")
