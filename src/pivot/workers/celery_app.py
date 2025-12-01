from __future__ import annotations

import os

try:
    from celery import Celery
    from .. import config

    celery_app = Celery(
        "pivot",
        broker=config.REDIS_URL,
        backend=config.REDIS_URL,
    )

    celery_app.conf.update(
        task_default_queue="ingest",
        task_time_limit=600,
        task_soft_time_limit=540,
    )

    # Ensure tasks module is imported so Celery can register task definitions
    from . import tasks  # noqa: E402,F401

except Exception:  # pragma: no cover - provide a stub for environments without celery
    class _DummyAsyncResult:
        def __init__(self):
            self.id = "test"

    class _DummyCeleryApp:
        def __init__(self):
            self.conf = {}

        def task(self, *args, **kwargs):
            # Return a decorator that attaches apply_async to the function
            def _decorator(func):
                def _wrapper(*f_args, **f_kwargs):
                    return func(*f_args, **f_kwargs)

                def apply_async(args=None, queue=None, **kw):
                    return _DummyAsyncResult()

                # attach apply_async on the wrapper so code using .apply_async works
                _wrapper.apply_async = apply_async
                return _wrapper

            return _decorator

    celery_app = _DummyCeleryApp()

    # Import tasks to ensure names exist (tasks will use the stub decorator)
    try:
        from . import tasks  # noqa: E402,F401
    except Exception:
        # If tasks import fails in this environment, ignore — tests that need tasks can patch behavior
        pass
