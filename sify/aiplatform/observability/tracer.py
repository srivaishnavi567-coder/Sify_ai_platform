# # sify/aiplatform/observability/tracer.py

# from time import time
# from typing import Dict, Any
# from langfuse import Langfuse
# from .config import get_langfuse_config

# _tracer = None


# # ------------------------------------------------------------------
# # No-op tracer (when langfuse disabled)
# # ------------------------------------------------------------------

# class NoOpSpan:
#     def end(self, *args, **kwargs):
#         pass


# class NoOpTracer:
#     def start_span(self, *args, **kwargs):
#         return NoOpSpan()

#     def flush(self):
#         pass


# # ------------------------------------------------------------------
# # Langfuse SPAN (no update method!)
# # ------------------------------------------------------------------

# class LangfuseSpan:
#     def __init__(self, client: Langfuse, name: str, input: Dict[str, Any]):
#         self.client = client
#         self.start_ts = time()

#         # Span context
#         self.ctx = client.start_as_current_observation(
#             as_type="span",
#             name=name,
#             input=input,
#         )
#         self.ctx.__enter__()

#     def end(self, output=None, status: str = "success"):
#         # Spans in Langfuse Python DO NOT support update calls
#         # Just close the observation safely
#         self.ctx.__exit__(None, None, None)


# # ------------------------------------------------------------------
# # Tracer wrapper
# # ------------------------------------------------------------------

# class LangfuseTracer:
#     def __init__(self, client: Langfuse):
#         self.client = client

#     def start_span(self, name: str, input: Dict[str, Any]):
#         return LangfuseSpan(self.client, name, input)

#     def flush(self):
#         self.client.flush()


# # ------------------------------------------------------------------
# # Factory
# # ------------------------------------------------------------------

# def get_tracer():
#     global _tracer

#     if _tracer is not None:
#         return _tracer

#     cfg = get_langfuse_config()
#     if not cfg or not cfg.enabled:
#         _tracer = NoOpTracer()
#         return _tracer

#     try:
#         client = Langfuse(
#             public_key=cfg.public_key,
#             secret_key=cfg.secret_key,
#             host=cfg.host,
#         )
#         _tracer = LangfuseTracer(client)
#         return _tracer
#     except Exception:
#         _tracer = NoOpTracer()
#         return _tracer

# sify/aiplatform/observability/tracer.py

from langfuse import Langfuse, propagate_attributes
from typing import Dict, Any, Optional
from .client import get_langfuse_client
from .context import langfuse_context
_tracer = None
_user_id = None
_session_id = None




# --------------------------------------------------
# Identity (set once by MaaS)
# --------------------------------------------------
def set_langfuse_identity(user_id=None, session_id=None):
    global _user_id, _session_id
    _user_id = user_id
    _session_id = session_id



# --------------------------------------------------
# No-op versions
# --------------------------------------------------
class NoOpSpan:
    def generation(self, **_): pass
    def end(self, *_, **__): pass


class NoOpTracer:
    def __call__(self, *_, **__): return NoOpSpan()
    def flush(self): pass


# --------------------------------------------------
# REAL Span object (IMPORTANT)
# --------------------------------------------------
class TracedSpan:
    def __init__(self, client: Langfuse, name: str, input: Dict[str, Any]):
        self.client = client

        # 🔥 THIS is where user/session is injected
        self._ctx = langfuse_context(user_id=_user_id, session_id=_session_id)

        self._ctx.__enter__()

        self._span_ctx = client.start_as_current_observation(
            as_type="span",
            name=name,
            input=input,
        )
        self._root = self._span_ctx.__enter__()

    # -----------------------------
    # Generation (matches manual)
    # -----------------------------
    def generation(
        self,
        *,
        model,
        input,
        output,
        usage=None,
        cost_details=None,
    ):
        with self._root.start_as_current_observation(
            as_type="generation",
            name="model-generation",
            model=model,
            input=input,
        ):
            self.client.update_current_generation(
                output={
                    "role": "assistant",
                    "content": output,
                },
                usage_details=usage,
                cost_details=cost_details,
            )

    # -----------------------------
    # End span
    # -----------------------------
    def end(self, *_, **__):
        # Close span
        self._span_ctx.__exit__(None, None, None)
        # Close identity context
        self._ctx.__exit__(None, None, None)


# --------------------------------------------------
# Tracer
# --------------------------------------------------
class LangfuseTracer:
    class LangfuseTracer:
        def __init__(self, client: Langfuse):
            self.client = client

        def start_span(self, name: str, input: Dict[str, Any]):
            return TracedSpan(self.client, name, input)

        def flush(self):
            self.client.flush()


# --------------------------------------------------
# Factory
# --------------------------------------------------
_tracer = None


def get_tracer():
    global _tracer
    if _tracer:
        return _tracer

    client = get_langfuse_client()
    if not client:
        _tracer = NoOpTracer()
    else:
        _tracer = LangfuseTracer()

    return _tracer






