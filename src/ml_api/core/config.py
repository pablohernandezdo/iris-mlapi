from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env: str
    app_name: str
    model_blob_url: str  # https://<account>.blob.core.windows.net/<container>/<blob>
    azure_client_id: str | None = (
        None  # user-assigned managed identity client ID; unset locally
    )

    db_url: SecretStr
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings():
    return Settings()  # type:ignore
