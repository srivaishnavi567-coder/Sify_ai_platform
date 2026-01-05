# sify/aiplatform/observability/tracer.py

from typing import Optional, Dict, Any
from langfuse import Langfuse
from .config import get_langfuse_config

_tracer = None


# ------------------------------------------------------------------
# No-Op Tracer (when Langfuse disabled)
# ------------------------------------------------------------------

class NoOpSpan:
    def end(self, *args, **kwargs):
        pass


class NoOpTracer:
    def start_span(self, *args, **kwargs):
        return NoOpSpan()


# ------------------------------------------------------------------
# Langfuse Tracer
# ------------------------------------------------------------------

class LangfuseTracer:
    def __init__(self, client: Langfuse):
        self.client = client

    def start_span(self, name: str, input: Dict[str, Any]):
        return self.client.span(
            name=name,
            input=input,
        )

    def flush(self):
        try:
            self.client.flush()
        except Exception:
            pass


# ------------------------------------------------------------------
# PUBLIC FACTORY (THIS WAS MISSING ❗)
# ------------------------------------------------------------------

def get_tracer():
    """
    Returns a singleton tracer.
    - LangfuseTracer if enabled
    - NoOpTracer otherwise
    """
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

