# sify/aiplatform/observability/tracer.py

from typing import Dict, Any
from time import time
from langfuse import Langfuse, propagate_attributes
from .config import get_langfuse_config

_tracer = None


# ---------------------------------------------------------------------
# No-op implementations
# ---------------------------------------------------------------------

class NoOpSpan:
    def end(self, *args, **kwargs):
        pass


class NoOpTracer:
    def start_span(self, *args, **kwargs):
        return NoOpSpan()

    def flush(self):
        pass


# ---------------------------------------------------------------------
# Langfuse span wrapper (CORRECT Python SDK usage)
# ---------------------------------------------------------------------

class LangfuseSpan:
    def __init__(self, client: Langfuse, name: str, input: Dict[str, Any]):
        self.client = client
        self.name = name
        self.input = input
        self.start_ts = time()

        # Start span using context manager
        self.ctx = self.client.start_as_current_observation(
            as_type="span",
            name=name,
            input=input,
        )
        self.root = self.ctx.__enter__()

    def end(self, output=None, status: str = "success"):
        duration_ms = round((time() - self.start_ts) * 1000, 2)

        # Correct way in Python SDK
        self.client.update_current_observation(
            output=output,
            metadata={
                "status": status,
                "duration_ms": duration_ms,
            },
        )

        # Close span
        self.ctx.__exit__(None, None, None)


# ---------------------------------------------------------------------
# Tracer
# ---------------------------------------------------------------------

class LangfuseTracer:
    def __init__(self, client: Langfuse):
        self.client = client

    def start_span(self, name: str, input: Dict[str, Any]):
        return LangfuseSpan(self.client, name, input)

    def flush(self):
        self.client.flush()


# ---------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------

def get_tracer():
    global _tracer

    if _tracer is not None:
        return _tracer

    cfg = get_langfuse_config()
    if not cfg or not cfg.enabled:
        _tracer = NoOpTracer()
        return _tracer

    try:
        client = Langfuse(
            public_key=cfg.public_key,
            secret_key=cfg.secret_key,
            host=cfg.host,
        )
        _tracer = LangfuseTracer(client)
        return _tracer
    except Exception:
        _tracer = NoOpTracer()
        return _tracer

