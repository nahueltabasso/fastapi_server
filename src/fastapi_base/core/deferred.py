from collections.abc import Awaitable, Callable

from fastapi import BackgroundTasks


class DeferredTasks:
    """Tasks that run after send the response.
    The different services add tasks to run after the transaction is closed.
    """

    def __init__(self, tasks: BackgroundTasks) -> None:
        self._tasks = tasks

    def add[**P](
        self, fn: Callable[P, Awaitable[None]], *args: P.args, **kwargs: P.kwargs
    ) -> None:
        self._tasks.add_task(fn, *args, **kwargs)
