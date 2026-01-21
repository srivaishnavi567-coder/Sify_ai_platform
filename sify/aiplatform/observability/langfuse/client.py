
from typing import Optional
from langfuse import Langfuse
from sify.aiplatform.observability.langfuse.config import get_langfuse_config
_client: Optional[Langfuse] = None


def get_langfuse_client() -> Optional[Langfuse]:
    global _client
    cfg = get_langfuse_config()

    if not cfg.enabled:
        return None

    if _client:
        return _client
    app_name = detect_app_name()
    _client = Langfuse(
        host=cfg.host,
        public_key=cfg.public_key,
        secret_key=cfg.secret_key,
    )
    return _client

