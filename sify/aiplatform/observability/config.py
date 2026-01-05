from dataclasses import dataclass

@dataclass
class LangfuseConfig:
    enabled: bool = False
    host: str | None = None
    public_key: str | None = None
    secret_key: str | None = None


_langfuse_config = LangfuseConfig()


def configure_langfuse(
    *,
    enabled: bool,
    host: str | None = None,
    public_key: str | None = None,
    secret_key: str | None = None,
):
    _langfuse_config.enabled = enabled
    _langfuse_config.host = host
    _langfuse_config.public_key = public_key
    _langfuse_config.secret_key = secret_key


def get_langfuse_config() -> LangfuseConfig:
    return _langfuse_config

