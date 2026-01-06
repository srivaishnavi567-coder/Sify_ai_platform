# from .client import get_langfuse_client


# class TraceSpan:
#     def __init__(self, root_span):
#         self.root = root_span
#         self.langfuse = get_langfuse_client()

#     def generation(
#         self,
#         *,
#         model: str,
#         input,
#         call_fn,
#         usage_fn=None,
#         cost_details=None,
#     ):
#         if not self.root or not self.langfuse:
#             return call_fn()

#         with self.root.start_as_current_observation(
#             as_type="generation",
#             name="model-generation",
#             model=model,
#             input=input,
#         ):
#             output = call_fn()

#             usage = usage_fn(output) if usage_fn else None

#             self.langfuse.update_current_generation(
#                 output={
#                     "role": "assistant",
#                     "content": output,
#                 },
#                 usage_details=usage,
#                 cost_details=cost_details,
#             )

#             return output
from time import time
from typing import Any, Dict
from langfuse import propagate_attributes


# ---------------------------------------------------------
# NO-OP SPAN
# ---------------------------------------------------------

class NoOpSpan:
    def generation(self, **kwargs):
        pass

    def end(self, **kwargs):
        pass


# ---------------------------------------------------------
# REAL LANGFUSE SPAN
# ---------------------------------------------------------

class TracedSpan:
    def __init__(
        self,
        *,
        client,
        name: str,
        input: Dict[str, Any],
        user_id: str | None,
        session_id: str | None,
    ):
        self.client = client
        self.name = name
        self.input = input
        self.start_ts = time()

        attrs = {}
        if user_id:
            attrs["user_id"] = user_id
        if session_id:
            attrs["session_id"] = session_id

        self._ctx = propagate_attributes(**attrs)
        self._ctx.__enter__()

        self._span = client.start_as_current_observation(
            as_type="span",
            name=name,
            input=input,
        )
        self._span.__enter__()

    # -----------------------------------------------------
    # GENERATION
    # -----------------------------------------------------

    def generation(
        self,
        *,
        model: str,
        input: Any,
        output: Any,
        usage: Dict[str, Any] | None = None,
        cost: Dict[str, Any] | None = None,
    ):
        with self.client.start_as_current_observation(
            as_type="generation",
            name="model-generation",
            model=model,
            input=input,
        ):
            self.client.update_current_generation(
                output=output,
                usage_details=usage,
                cost_details=cost,
            )

    # -----------------------------------------------------
    # END
    # -----------------------------------------------------

    def end(self, **_):
        self._span.__exit__(None, None, None)
        self._ctx.__exit__(None, None, None)


