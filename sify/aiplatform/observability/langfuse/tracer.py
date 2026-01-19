

from typing import Dict, Any
from langfuse import Langfuse, propagate_attributes

from sify.aiplatform.observability.langfuse.client import get_langfuse_client

# --------------------------------------------------
# Globals
# --------------------------------------------------
_tracer = None
_user_id = None
_session_id = None


# --------------------------------------------------
# Identity
# --------------------------------------------------
def set_langfuse_identity(user_id=None, session_id=None):
    global _user_id, _session_id
    _user_id = user_id
    _session_id = session_id


# --------------------------------------------------
# No-op fallback
# --------------------------------------------------
class NoOpSpan:
    def generation(self, **_): pass
    def end(self): pass


class NoOpTracer:
    def start_span(self, *_, **__):
        return NoOpSpan()

    def flush(self): pass


# --------------------------------------------------
# Real span
# --------------------------------------------------
class TracedSpan:
    def __init__(self, client: Langfuse, name: str, input: Dict[str, Any]):
        self.client = client

        # 🔥 Attributes MUST be active before span creation
        self._attr_ctx = propagate_attributes(
            user_id=_user_id,
            session_id=_session_id,
        )
        self._attr_ctx.__enter__()

        self._span_ctx = client.start_as_current_observation(
            as_type="span",
            name=name,
            input=input,
        )
        self._root = self._span_ctx.__enter__()

    def generation(self, *, model, input, output, usage=None, cost_details=None):
        with propagate_attributes(
            user_id=_user_id,
            session_id=_session_id,
        ):
            with self._root.start_as_current_observation(
                as_type="generation",
                name="model-generation",
                model=model,
                input=input,
            ):
                self.client.update_current_generation(
                    model=model, 
                    output={
                        "role": "assistant",
                        "content": output,
                    },
                    usage_details=usage,
                    cost_details=cost_details,
                )

    def end(self):
        self._span_ctx.__exit__(None, None, None)
        self._attr_ctx.__exit__(None, None, None)


# --------------------------------------------------
# Tracer wrapper
# --------------------------------------------------
class LangfuseTracer:
    def __init__(self, client: Langfuse):
        self.client = client

    def start_span(self, name: str, input: Dict[str, Any]):
        return TracedSpan(self.client, name, input)

    def flush(self):
        self.client.flush()


# --------------------------------------------------
# FACTORY (THIS IS WHAT YOU ARE MISSING)
# --------------------------------------------------
def get_tracer():
    global _tracer
    if _tracer:
        return _tracer

    client = get_langfuse_client()
    if not client:
        _tracer = NoOpTracer()
    else:
        _tracer = LangfuseTracer(client)

    return _tracer









