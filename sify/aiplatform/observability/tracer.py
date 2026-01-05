from contextlib import contextmanager
from time import time
from langfuse import propagate_attributes
from .span import TraceSpan
from .client import get_langfuse_client


class LangfuseTracer:
    def __init__(self, service_name: str, user_id=None, session_id=None):
        self.service_name = service_name
        self.user_id = user_id
        self.session_id = session_id
        self.client = get_langfuse_client()

    @contextmanager
    def trace(self, name: str):
        if not self.client:
            yield TraceSpan(None)
            return

        start_ts = time()

        with self.client.start_as_current_observation(
            as_type="trace",
            name=name,
        ) as trace:
            trace.update(metadata={"service": self.service_name})

            with propagate_attributes(
                user_id=self.user_id,
                session_id=self.session_id,
            ):
                try:
                    yield TraceSpan(trace)
                finally:
                    trace.update(
                        metadata={
                            "duration_ms": round((time() - start_ts) * 1000, 2)
                        }
                    )
