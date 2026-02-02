import functools
from logging import Logger
from time import sleep
from typing import Any, Callable, Optional, Tuple


def retry_on_exception(
    func_call: Optional[Callable[[], Any]] = None,
    retries: int = 5,
    delay: float = 0,
    exceptions: Tuple = (Exception,),
    logger: Logger = None,
    exception_handler: Callable[..., Any] = None,
) -> Any:
    """
    Can be used two ways:

    1) As a decorator (must include the () even if you want all defaults):
       @retry_on_exception(retries=3, delay=1, exceptions=(OperationalError,), logger=log)
       def foo(...): ...

    2) As a direct call:
       result = retry_on_exception(lambda: foo(...), retries=3, delay=1)
    """

    def _retry(func: Callable[..., Any], *args, **kwargs) -> Any:
        attempt = 0
        while True:
            try:
                attempt += 1
                return func(*args, **kwargs)
            except exceptions as exc:
                if logger:
                    logger.exception(f"[{func.__name__}] attempt {attempt} failed: {exc!r}")
                if exception_handler:
                    exception_handler()
                if attempt >= retries:
                    raise
                if delay:
                    sleep(delay)
                if logger:
                    logger.info(f"[{func.__name__}] retrying attempt {attempt+1}/{retries}...")

    # 1) direct invocation: func_call is not None
    if func_call is not None:
        # we expect func_call to be a zero-arg callable
        return _retry(func_call)

    # 2) used as decorator (func_call is None) → return a decorator
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return _retry(func, *args, **kwargs)

        return wrapper

    return decorator
