"""
Пример добавления Qdrant настроек в существующий config.

Скопируйте нужные части в ваш config.py.
"""

from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Настройки приложения.

    Добавьте эти поля в ваш существующий Settings класс.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # =========================================================================
    # Qdrant Settings
    # =========================================================================
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str | None = None
    qdrant_url: str | None = None  # Для Cloud режима
    qdrant_local_path: str | None = None  # Для Embedded режима

    @computed_field
    @property
    def is_qdrant_local_mode(self) -> bool:
        """True если используется embedded режим (без Docker)."""
        return self.qdrant_local_path is not None

    def get_qdrant_client_kwargs(self) -> dict:
        """
        Параметры для QdrantClient.connect().

        Returns:
            dict с параметрами подключения.
        """
        if self.qdrant_local_path:
            return {"path": self.qdrant_local_path}

        if self.qdrant_url:
            return {
                "url": self.qdrant_url,
                "api_key": self.qdrant_api_key,
            }

        return {
            "host": self.qdrant_host,
            "port": self.qdrant_port,
            "api_key": self.qdrant_api_key,
        }


@lru_cache
def get_settings() -> Settings:
    """Кэшированный singleton для настроек."""
    return Settings()


settings = get_settings()
