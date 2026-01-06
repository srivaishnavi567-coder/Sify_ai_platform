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
from .client import get_langfuse_client, langfuse_attributes


class NoOpSpan:
    def generation(self, **_):
        pass

    def end(self):
        pass


class TracedSpan:
    def __init__(self, client, name, input):
        self.client = client
        self.ctx = client.start_as_current_observation(
            as_type="span",
            name=name,
            input=input,
        )
        self.ctx.__enter__()

    def generation(
        self,
        *,
        model: str,
        input,
        output,
        usage: Dict[str, int] | None,
        cost: Dict[str, float] | None = None,
    ):
        self.client.generation(
            name="model-generation",
            model=model,
            input=input,
            output=output,
            usage_details=usage,
            cost_details=cost,
        )

    def end(self):
        self.ctx.__exit__(None, None, None)


def get_tracer():
    client = get_langfuse_client()
    attrs = langfuse_attributes()

    if not client:
        return lambda *_: NoOpSpan()

    def start_span(name: str, input: Dict[str, Any]):
        if attrs:
            with attrs:
                return TracedSpan(client, name, input)
        return TracedSpan(client, name, input)

    return start_span

