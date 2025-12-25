"""
Пример интеграции Qdrant в lifespan FastAPI приложения.

Скопируйте нужные части в ваш main.py.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Импорты из модуля qdrant
from qdrant import router as qdrant_router
from qdrant.client import qdrant_client
from qdrant.exceptions import DomainError

# Ваш config (см. config_snippet.py)
# from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan manager для FastAPI.

    Управляет подключением к Qdrant при старте/остановке приложения.
    """
    # ==========================================================================
    # Startup
    # ==========================================================================

    # Вариант 1: Простое подключение
    await qdrant_client.connect(host="localhost", port=6333)

    # Вариант 2: Из настроек (раскомментируйте)
    # kwargs = settings.get_qdrant_client_kwargs()
    # await qdrant_client.connect(**kwargs)

    # Вариант 3: Cloud режим
    # await qdrant_client.connect(
    #     url="https://xxx.cloud.qdrant.io:6333",
    #     api_key="your-api-key"
    # )

    # Вариант 4: Local/Embedded режим (без Docker)
    # await qdrant_client.connect(path="./qdrant_storage")

    yield

    # ==========================================================================
    # Shutdown
    # ==========================================================================
    await qdrant_client.close()


# =============================================================================
# Application Factory
# =============================================================================
def create_app() -> FastAPI:
    """
    Фабрика приложения FastAPI.

    Returns:
        Сконфигурированное FastAPI приложение.
    """
    app = FastAPI(
        title="My API with Qdrant",
        version="1.0.0",
        lifespan=lifespan,
    )

    # =========================================================================
    # Exception Handlers
    # =========================================================================
    @app.exception_handler(DomainError)
    async def domain_error_handler(request, exc: DomainError):
        """Конвертация доменных исключений в HTTP ответы."""
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )

    # =========================================================================
    # Routers
    # =========================================================================
    # Подключение Qdrant роутера
    app.include_router(qdrant_router, prefix="/api/v1")

    # Ваши другие роутеры
    # app.include_router(users_router, prefix="/api/v1")
    # app.include_router(products_router, prefix="/api/v1")

    # =========================================================================
    # Health Check
    # =========================================================================
    @app.get("/health")
    async def health_check():
        """Проверка состояния приложения и Qdrant."""
        qdrant_health = await qdrant_client.health_check()
        return {
            "status": "healthy" if qdrant_health["status"] == "healthy" else "degraded",
            "qdrant": qdrant_health,
        }

    return app


# =============================================================================
# Entry Point
# =============================================================================
app = create_app()

# Запуск: uvicorn main:app --reload
