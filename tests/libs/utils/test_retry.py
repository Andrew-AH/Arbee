import pytest

from libs.utils.retry import retry_on_exception


def test_retry_on_exception_success():
    """
    Test that retry_on_exception returns the correct value without any retries if no exception is raised.
    """
    assert retry_on_exception(lambda: 42) == 42


def test_retry_on_exception_raises():
    """
    Test that retry_on_exception raises the expected exception after the specified number of retries.
    """
    with pytest.raises(ValueError):
        retry_on_exception(
            lambda: (_ for _ in ()).throw(ValueError("Test exception")),
            retries=2,
            exceptions=(ValueError,),
        )


def test_retry_on_exception_retries():
    """
    Test that retry_on_exception retries the correct number of times before succeeding.
    """
    attempts = 0

    def func_call():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("Test exception")
        return "success"

    assert retry_on_exception(func_call, retries=3, exceptions=(ValueError,)) == "success"
    assert attempts == 3


def test_retry_on_exception_calls_exception_handler():
    """
    Test that the exception_handler is called each time an exception is raised.
    """
    attempts = 0

    def func_call():
        raise ValueError("Test exception")

    def exception_handler():
        nonlocal attempts
        attempts += 1

    with pytest.raises(ValueError):
        retry_on_exception(
            func_call, retries=3, exceptions=(ValueError,), exception_handler=exception_handler
        )

    assert attempts == 3


def test_retry_on_exception_decorator_success_after_retry():
    state = {"count": 0}

    @retry_on_exception(retries=3, delay=0, exceptions=(ValueError,))
    def test_func():
        state["count"] += 1
        if state["count"] < 2:
            raise ValueError()
        return "ok"

    assert test_func() == "ok"
    assert state["count"] == 2


def test_retry_on_exception_decorator_exhausts_retries():
    state = {"count": 0}

    @retry_on_exception(retries=2, delay=0, exceptions=(ValueError,))
    def test_func():
        state["count"] += 1
        raise ValueError()

    with pytest.raises(ValueError):
        test_func()
    assert state["count"] == 2
