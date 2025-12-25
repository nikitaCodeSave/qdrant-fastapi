"""
Конфигурация приложения.

Загружает настройки из переменных окружения и .env файла.
Использует pydantic-settings для валидации и типизации.

Example:
    >>> from src.config import settings
    >>> print(settings.qdrant_url)
    'http://localhost:6333'
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Настройки приложения.

    Приоритет загрузки:
    1. Переменные окружения (высший)
    2. Файл .env
    3. Значения по умолчанию (низший)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------
    project_name: str = Field(
        default="Qdrant RAG Service",
        description="Название проекта для API docs",
    )
    version: str = Field(default="0.1.0")
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Окружение приложения",
    )

    # -------------------------------------------------------------------------
    # API
    # -------------------------------------------------------------------------
    api_prefix: str = Field(
        default="/api/v1",
        description="Префикс для API endpoints",
    )

    # -------------------------------------------------------------------------
    # Qdrant Connection
    # -------------------------------------------------------------------------
    qdrant_host: str = Field(default="localhost")
    qdrant_port: int = Field(default=6333, ge=1, le=65535)
    qdrant_grpc_port: int = Field(default=6334, ge=1, le=65535)
    qdrant_api_key: str | None = Field(default=None)
    qdrant_prefer_grpc: bool = Field(
        default=True,
        description="gRPC быстрее REST для bulk операций",
    )
    qdrant_timeout: float = Field(default=30.0, gt=0)
    qdrant_https: bool = Field(
        default=False,
        description="Использовать HTTPS для подключения к Qdrant",
    )

    # Локальный режим (embedded, без Docker)
    qdrant_local_path: str | None = Field(
        default=None,
        description="Путь для локального хранилища. Если указан — Docker не нужен.",
    )

    # -------------------------------------------------------------------------
    # Qdrant Defaults
    # -------------------------------------------------------------------------
    qdrant_default_collection: str = Field(default="documents")
    qdrant_vector_size: int = Field(
        default=1024,
        description="1024 для e5-large, 1536 для OpenAI",
    )
    qdrant_distance: Literal["Cosine", "Euclid", "Dot"] = Field(default="Cosine")

    # -------------------------------------------------------------------------
    # Computed Fields
    # -------------------------------------------------------------------------
    @computed_field
    @property
    def qdrant_url(self) -> str:
        """URL для REST API Qdrant."""
        scheme = "https" if self.qdrant_https else "http"
        return f"{scheme}://{self.qdrant_host}:{self.qdrant_port}"

    @computed_field
    @property
    def is_local_mode(self) -> bool:
        """Использовать embedded Qdrant без сервера."""
        return self.qdrant_local_path is not None

    @computed_field
    @property
    def is_production(self) -> bool:
        """Проверка production окружения."""
        return self.environment == "production"

    # -------------------------------------------------------------------------
    # Methods
    # -------------------------------------------------------------------------
    def get_qdrant_client_kwargs(self) -> dict:
        """
        Параметры для создания QdrantClient.

        Returns:
            Kwargs для AsyncQdrantClient.__init__()
        """
        if self.is_local_mode:
            return {"path": self.qdrant_local_path}

        return {
            "host": self.qdrant_host,
            "port": self.qdrant_port,
            "grpc_port": self.qdrant_grpc_port,
            "api_key": self.qdrant_api_key,
            "prefer_grpc": self.qdrant_prefer_grpc,
            "timeout": self.qdrant_timeout,
            "https": self.qdrant_https,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Получить закэшированные настройки (singleton).

    Для сброса кэша (в тестах):
        >>> get_settings.cache_clear()
    """
    return Settings()


# Глобальный экземпляр для удобного импорта
settings = get_settings()
