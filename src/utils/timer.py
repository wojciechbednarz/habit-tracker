"""Module for time measuring time of functions"""

import inspect
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class Timer:
    """
    Class implementing methods for context manager to measure function execution time.
    """

    def __init__(
        self, start_time: float | None = None, func: None | Callable[..., Any] = None, wall_clock_time: bool = True
    ) -> None:
        """
        Initialization of the Timer class with start and stop time.

        :start_time: Optional start time for the timer (default: None)
        :func: Optional function to be wrapped by the timer (default: None)
        :wall_clock_time: Flag to determine whether to use wall clock time or process time (default: True)
        :return: None
        """
        self.start_time: float | None = None
        if func:
            self.func = func
        self.get_time = time.perf_counter if wall_clock_time else time.process_time

    def __enter__(self) -> "Timer":
        """
        Start the timer when entering the context.

        :return: The Timer instance itself
        """
        self.start_time = self.get_time()
        return self

    def __exit__(self, *args: Any) -> None:
        """
        Stop the timer and log the elapsed time when exiting the context.

        :args: Any additional arguments (not used)
        :return: None
        """
        if self.start_time is not None:
            result = self.get_time() - self.start_time
            logger.info(f"Execution time: {result:.4f} seconds")
        else:
            logger.warning("Timer exited without being started.")

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        Call the wrapped function and log its execution time.

        :args: Positional arguments for the wrapped function
        :kwargs: Keyword arguments for the wrapped function
        :return: The result of the wrapped function
        """
        if inspect.iscoroutinefunction(self.func):

            @wraps(self.func)
            async def async_wrapper() -> Any:
                start = self.get_time()
                try:
                    await self.func(*args, **kwargs)
                finally:
                    end = self.get_time()
                    logger.info(f"{self.func.__name__}() execution time: {end - start:.4f} seconds")

            return async_wrapper()
        else:
            start = self.get_time()
            try:
                self.func(*args, **kwargs)
            finally:
                end = self.get_time()
                logger.info(f"{self.func.__name__}() execution time: {end - start:.4f} seconds")

    async def __aenter__(self) -> "Timer":
        """
        Start the timer when entering the asynchronous context.

        :return: The Timer instance itself
        """
        self.start_time = self.get_time()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """ "
        Stop the timer and log the elapsed time when exiting the asynchronous context.

        :args: Any additional arguments (not used)
        :return: None
        """
        if self.start_time is not None:
            result = self.get_time() - self.start_time
            logger.info(f"Execution time: {result:.4f} seconds")
        else:
            logger.warning("Timer exited without being started.")


def timer(func: Callable[..., Any]) -> Any:
    """
    Shortcut decorator to use the Timer class. Usage: @timer.

    :func: The function to be wrapped by the timer
    :return: The result of the wrapped function
    """
    return Timer(func=func)
