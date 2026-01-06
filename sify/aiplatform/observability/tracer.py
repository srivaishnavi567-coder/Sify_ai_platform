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

# sify/aiplatform/observability/tracer.py

from time import time
from typing import Dict, Any, Optional

from langfuse import Langfuse, propagate_attributes

from .client import get_langfuse_client
from .config import get_langfuse_config


# ============================================================
# No-Op Implementations (Langfuse disabled)
# ============================================================

class NoOpSpan:
    def generation(self, **kwargs):
        return None

    def end(self, **kwargs):
        pass


class NoOpTracer:
    def __call__(self, *args, **kwargs):
        return NoOpSpan()

    def flush(self):
        pass


# ============================================================
# Real Traced Span
# ============================================================

class TracedSpan:
    def __init__(self, client: Langfuse, name: str, input: Dict[str, Any]):
        self.client = client
        self.start_ts = time()

        # IMPORTANT: start span observation
        self._ctx = client.start_as_current_observation(
            as_type="span",
            name=name,
            input=input,
        )
        self._ctx.__enter__()

    # --------------------------------------------------------
    # Generation (THIS IS WHAT MaaS EXPECTS)
    # --------------------------------------------------------
    def generation(
        self,
        *,
        model: str,
        input,
        output,
        usage: Optional[Dict[str, Any]] = None,
        cost_details: Optional[Dict[str, Any]] = None,
    ):
        # Generation must be nested inside span
        with self.client.start_as_current_observation(
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

    # --------------------------------------------------------
    # End span
    # --------------------------------------------------------
    def end(self, **kwargs):
        self._ctx.__exit__(None, None, None)


# ============================================================
# Tracer Wrapper (callable)
# ============================================================

class LangfuseTracer:
    def __init__(self, client: Langfuse):
        self.client = client

    # THIS is why MaaS can do: self.tracer("name", data)
    def __call__(self, name: str, input: Dict[str, Any]):
        return TracedSpan(self.client, name, input)

    def flush(self):
        self.client.flush()


# ============================================================
# Factory (singleton)
# ============================================================

_tracer = None


def get_tracer():
    global _tracer

    if _tracer is not None:
        return _tracer

    cfg = get_langfuse_config()

    if not cfg or not cfg.enabled:
        _tracer = NoOpTracer()
        return _tracer

    try:
        client = get_langfuse_client()
        if not client:
            raise RuntimeError("Langfuse client not available")

        _tracer = LangfuseTracer(client)
        return _tracer

    except Exception:
        # Absolute safety fallback
        _tracer = NoOpTracer()
        return _tracer
