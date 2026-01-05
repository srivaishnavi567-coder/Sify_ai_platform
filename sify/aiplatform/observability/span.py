from .client import get_langfuse_client


class TraceSpan:
    def __init__(self, root_span):
        self.root = root_span
        self.langfuse = get_langfuse_client()

    def generation(
        self,
        *,
        model: str,
        input,
        call_fn,
        usage_fn=None,
        cost_details=None,
    ):
        if not self.root or not self.langfuse:
            return call_fn()

        with self.root.start_as_current_observation(
            as_type="generation",
            name="model-generation",
            model=model,
            input=input,
        ):
            output = call_fn()

            usage = usage_fn(output) if usage_fn else None

            self.langfuse.update_current_generation(
                output={
                    "role": "assistant",
                    "content": output,
                },
                usage_details=usage,
                cost_details=cost_details,
            )

            return output
