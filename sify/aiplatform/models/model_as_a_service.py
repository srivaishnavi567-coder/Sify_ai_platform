import json
import requests
from typing import Any, Dict, Generator, List, Optional, Union, BinaryIO

from sify.aiplatform.models.types import (
    ModelsListResponse,
    EmbeddingResponse,
    ChatCompletionResponse,
    ChatCompletionChunk,
    CompletionResponse,
    CompletionChunk,
    AudioTranscriptionResponse,
    AudioTranslationResponse,
    RerankResponse,
    APIError,
)

from sify.aiplatform.observability.tracer import (
    get_tracer,
    set_langfuse_identity,
)


class ModelAsAService:
    def __init__(
        self,
        api_key: str,
        model_id: str = None,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
    ):
        if not api_key or not api_key.strip():
             raise ValueError("API key must be provided and cannot be empty")

        self.base_url = "https://infinitai.sifymdp.digital/maas"
        self.api_key = api_key.strip()
        self.model_id = model_id.strip() if model_id else None

        
        set_langfuse_identity(user_id=user_id, session_id=session_id)
       

        self.tracer = get_tracer()






    # def __init__(self, api_key: str, model_id: str = None,  *,
    # user_id: str | None = None,
    # session_id: str | None = None,):
    #     if not api_key or not api_key.strip():
    #         raise ValueError("API key must be provided and cannot be empty")

    #     self.base_url = "https://infinitai.sifymdp.digital/maas"
    #     self.api_key = api_key.strip()
    #     self.model_id = model_id.strip() if model_id else None
        
    
    
    # ---------------------------------------------------------------------
    # INTERNAL REQUEST HANDLING
    # ---------------------------------------------------------------------

    def _send_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        form_data: Optional[Dict[str, Any]] = None,
        stream: bool = False,
        return_binary: bool = False,
    ) -> Union[Dict[str, Any], Generator[Dict[str, Any], None, None], bytes]:

        url = f"{self.base_url}{endpoint}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        if not files and not form_data:
            headers["Content-Type"] = "application/json"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=json_data,
                params=params,
                files=files,
                data=form_data,
                stream=stream,
                timeout=300,
            )

            if response.status_code >= 400:
                raise ValueError(
                    str(APIError(error=response.text, status_code=response.status_code))
                )

            if stream:
                return self._handle_stream_response(response)

            if return_binary:
                return response.content

            return {"result": response.json()}

        except requests.RequestException as e:
            raise ValueError(str(e))

    def _handle_stream_response(
        self, response
    ) -> Generator[Dict[str, Any], None, None]:
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                data = line.replace("data: ", "").strip()
                if data and data != "[DONE]":
                    yield json.loads(data)

    # ---------------------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------------------

    def _validate_required_params(self, params: Dict[str, Any]) -> None:
        for k, v in params.items():
            if v is None or (isinstance(v, str) and not v.strip()):
                raise ValueError(f"{k} must not be empty")

    def _validate_optional_params(self, params: Dict[str, Any]) -> None:
        for k, v in params.items():
            if isinstance(v, str) and not v.strip():
                raise ValueError(f"{k} must not be empty")

    # ---------------------------------------------------------------------
    # AUDIO
    # ---------------------------------------------------------------------

    def speech_to_text(self, file: BinaryIO, **kwargs) -> AudioTranscriptionResponse:
        if file is None:
            raise ValueError("File must be provided")

        span = self.tracer.start_span("maas.speech_to_text", {"model": self.model_id})

        try:
            response = self._send_request(
                "POST",
                "/v1/audio/transcriptions",
                files={"file": file},
                form_data={"model": self.model_id, **kwargs},
            )

            result = response["result"]

            span.generation(
                model=self.model_id,
                input="audio_file",
                output=result.get("text"),
                usage=result.get("usage"),
            )

            span.end()
            return AudioTranscriptionResponse.from_dict(result)
        except Exception as e:
            span.end()
            raise

    def audio_translation(self, file: BinaryIO, **kwargs) -> AudioTranslationResponse:
        if file is None:
            raise ValueError("File must be provided")

        span = self.tracer.start_span("maas.audio_translation", {"model": self.model_id})

        try:
            response = self._send_request(
                "POST",
                "/v1/audio/translations",
                files={"file": file},
                form_data={"model": self.model_id, **kwargs},
            )

            result = response["result"]

            span.generation(
                model=self.model_id,
                input="audio_file",
                output=result.get("text"),
                usage=result.get("usage"),
            )

            span.end()
            return AudioTranslationResponse.from_dict(result)
        except Exception as e:
            span.end()
            raise

    def text_to_speech(self, input_text: str, voice: str, **kwargs) -> bytes:
        self._validate_required_params({"input_text": input_text, "voice": voice})

        span = self.tracer.start_span("maas.text_to_speech", {"model": self.model_id})

        try:
            audio = self._send_request(
                "POST",
                "/v1/audio/speech",
                json_data={
                    "model": self.model_id,
                    "input": input_text,
                    "voice": voice,
                    **kwargs,
                },
                return_binary=True,
            )

            span.generation(
                model=self.model_id,
                input=input_text,
                output="binary_audio",
                usage=None,
            )

            span.end()
            return audio
        except Exception as e:
            span.end()
            raise

    # ---------------------------------------------------------------------
    # EMBEDDINGS
    # ---------------------------------------------------------------------

    def create_embeddings(
        self, input_data: Union[str, List[str]], **kwargs
    ) -> EmbeddingResponse:

        self._validate_required_params({"input": input_data})

        span = self.tracer.start_span("maas.embeddings", {"model": self.model_id})

        try:
            response = self._send_request(
                "POST",
                "/v1/embeddings",
                json_data={"model": self.model_id, "input": input_data, **kwargs},
            )

            result = response["result"]

            span.generation(
                model=self.model_id,
                input=input_data,
                output="embedding_vectors",
                usage=result.get("usage"),
            )

            span.end()
            return EmbeddingResponse.from_dict(result)
        except Exception as e:
            span.end()
            raise

    # ---------------------------------------------------------------------
    # CHAT COMPLETION
    # ---------------------------------------------------------------------

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        stream: bool = False,
        **kwargs,
    ) -> Union[
        ChatCompletionResponse, Generator[ChatCompletionChunk, None, None]
    ]:

        self._validate_required_params({"messages": messages})

        for msg in messages:
            if "role" not in msg or "content" not in msg:
                raise ValueError("Each message must have role and content")

        data = {
            "model": self.model_id,
            "messages": messages,
            "stream": stream,
            **kwargs,
        }

        span = self.tracer.start_span("maas.chat_completion", data)

        if not stream:
            try:
                response = self._send_request(
                    "POST",
                    "/v1/chat/completions",
                    json_data=data,
                )

                result = response["result"]
                output_text = result["choices"][0]["message"]["content"]

                span.generation(
                    model=self.model_id,
                    input=messages,
                    output=output_text,
                    usage=result.get("usage") if result.get("usage") else None,
                )

                span.end()
                return ChatCompletionResponse.from_dict(result)
            except Exception as e:
                span.end()
                raise

        def _stream_generator():
            collected = ""
            try:
                for chunk in self._send_request(
                    "POST",
                    "/v1/chat/completions",
                    json_data=data,
                    stream=True,
                ):
                    if "choices" in chunk:
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            collected += content
                    yield ChatCompletionChunk.from_dict(chunk)

                span.generation(
                    model=self.model_id,
                    input=messages,
                    output=collected,
                    usage=None,
                )

                span.end()
            except Exception as e:
                span.end()
                raise

        return _stream_generator()

    # ---------------------------------------------------------------------
    # COMPLETION
    # ---------------------------------------------------------------------

    def completion(
        self,
        prompt: str,
        stream: bool = False,
        **kwargs,
    ) -> Union[
        CompletionResponse, Generator[CompletionChunk, None, None]
    ]:

        self._validate_required_params({"prompt": prompt})

        data = {
            "model": self.model_id,
            "prompt": prompt,
            "stream": stream,
            **kwargs,
        }

        span = self.tracer.start_span("maas.completion", data)

        if not stream:
            try:
                response = self._send_request(
                    "POST",
                    "/v1/completions",
                    json_data=data,
                )

                result = response["result"]
                output_text = result["choices"][0]["text"]

                span.generation(
                    model=self.model_id,
                    input=prompt,
                    output=output_text,
                    usage=result.get("usage"),
                )

                span.end()
                return CompletionResponse.from_dict(result)
            except Exception as e:
                span.end()
                raise

        def _stream_generator():
            collected = ""
            try:
                for chunk in self._send_request(
                    "POST",
                    "/v1/completions",
                    json_data=data,
                    stream=True,
                ):
                    if "choices" in chunk:
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            collected += content
                    yield CompletionChunk.from_dict(chunk)

                span.generation(
                    model=self.model_id,
                    input=prompt,
                    output=collected,
                    usage=None,
                )

                span.end()
            except Exception as e:
                span.end()
                raise

        return _stream_generator()

    # ---------------------------------------------------------------------
    # MODELS & RERANK
    # ---------------------------------------------------------------------

    def list_models(self) -> ModelsListResponse:
        response = self._send_request("GET", "/v1/models")
        return ModelsListResponse.from_dict(response["result"])

    def rerank(
        self, query: str, documents: List[Union[str, Dict[str, Any]]], **kwargs
    ) -> RerankResponse:

        self._validate_required_params({"query": query, "documents": documents})

        response = self._send_request(
            "POST",
            "/v1/rerank",
            json_data={
                "model": self.model_id,
                "query": query,
                "documents": documents,
                **kwargs,
            },
        )
        return RerankResponse.from_dict(response["result"])
