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
from time import time
from typing import Dict, Any
from langfuse import Langfuse
from .config import get_langfuse_config
from .client import get_langfuse_client
from .context import langfuse_context
from .span import TraceSpan

_tracer = None


# -----------------------
# No-op
# -----------------------

class NoOpSpan:
    def generation(self, *args, **kwargs):
        return kwargs["call_fn"]()

    def end(self, *args, **kwargs):
        pass


class NoOpTracer:
    def start_span(self, *args, **kwargs):
        return NoOpSpan()

    def flush(self):
        pass


# -----------------------
# Langfuse
# -----------------------

class LangfuseTracer:
    def __init__(self, client: Langfuse, user_id=None, session_id=None):
        self.client = client
        self.user_id = user_id
        self.session_id = session_id

    def start_span(self, name: str, input: Dict[str, Any]):
        ctx = langfuse_context(
            user_id=self.user_id,
            session_id=self.session_id,
        )
        ctx.__enter__()

        obs = self.client.start_as_current_observation(
            as_type="span",
            name=name,
            input=input,
        )
        obs.__enter__()

        return TraceSpan(obs)

    def flush(self):
        self.client.flush()


# -----------------------
# Factory
# -----------------------

def get_tracer(user_id=None, session_id=None):
    global _tracer

    cfg = get_langfuse_config()
    if not cfg or not cfg.enabled:
        return NoOpTracer()

    client = get_langfuse_client()
    if not client:
        return NoOpTracer()

    return LangfuseTracer(
        client,
        user_id=user_id,
        session_id=session_id,
    )
