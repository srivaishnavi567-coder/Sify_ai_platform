from typing import Dict, Any
from .config import get_langfuse_config

_tracer = None



# No-Op implementations


class NoOpSpan:
    def end(self, *args, **kwargs):
        pass


class NoOpTracer:
    def start_span(self, *args, **kwargs):
        return NoOpSpan()

    def span(self, *args, **kwargs):
        return self.start_span(*args, **kwargs)

# Langfuse Tracer


class LangfuseTracer:
    def __init__(self, client):
        self.client = client

    def start_span(self, name: str, input: Dict[str, Any]):
        return self.client.span(
            name=name,
            input=input,
        )


def get_tracer():
    global _tracer

    if _tracer is not None:
        return _tracer

    cfg = get_langfuse_config()
    if not cfg or not cfg.enabled:
        _tracer = NoOpTracer()
        return _tracer

    try:
        from langfuse import Langfuse

        client = Langfuse(
            public_key=cfg.public_key,
            secret_key=cfg.secret_key,
            host=cfg.host,
        )

        _tracer = LangfuseTracer(client)
        return _tracer

    except Exception:
        # Langfuse missing or misconfigured → safe fallback
        _tracer = NoOpTracer()
        return _tracer
