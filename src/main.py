"""
Точка входа FastAPI приложения.

Паттерны:
- Application Factory: create_application() для тестов
- Lifespan: управление lifecycle ресурсов
- Централизованный exception_handler для DomainError

Запуск:
    uvicorn src.main:app --reload
"""

from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.config import settings
from src.qdrant import router as qdrant_router
from src.qdrant.client import qdrant_client
from src.shared.exceptions import DomainError
from src.shared.schemas import ErrorResponse, HealthResponse, ServiceHealth

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG if not settings.is_production else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# =============================================================================
# Lifespan
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Управление жизненным циклом приложения.

    Startup:
        - Подключение к Qdrant

    Shutdown:
        - Закрытие соединений
    """
    # -------------------------------------------------------------------------
    # STARTUP
    # -------------------------------------------------------------------------
    logger.info(
        "🚀 Starting %s v%s [%s]",
        settings.project_name,
        settings.version,
        settings.environment,
    )

    # Подключение к Qdrant
    await qdrant_client.connect()

    yield

    # -------------------------------------------------------------------------
    # SHUTDOWN
    # -------------------------------------------------------------------------
    logger.info("👋 Shutting down %s", settings.project_name)

    await qdrant_client.close()


# =============================================================================
# Application Factory
# =============================================================================
def create_application() -> FastAPI:
    """
    Создаёт и конфигурирует FastAPI приложение.

    Returns:
        Сконфигурированный экземпляр FastAPI.
    """
    app = FastAPI(
        title=settings.project_name,
        version=settings.version,
        lifespan=lifespan,
        # Отключаем docs в production
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
    )

    # -------------------------------------------------------------------------
    # Exception Handlers
    # -------------------------------------------------------------------------
    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        """
        Централизованная обработка доменных исключений.

        Конвертирует DomainError в HTTP ответ с соответствующим статус-кодом.
        """
        logger.warning(
            "DomainError: %s [%s] - %s",
            exc.error_code,
            exc.status_code,
            exc.message,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=exc.error_code,
                message=exc.message,
                details=exc.details,
            ).model_dump(),
        )

    # -------------------------------------------------------------------------
    # Routers
    # -------------------------------------------------------------------------
    # Qdrant домен
    app.include_router(qdrant_router, prefix=settings.api_prefix)

    # -------------------------------------------------------------------------
    # Root Endpoints
    # -------------------------------------------------------------------------
    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        """Корневой endpoint."""
        return {
            "service": settings.project_name,
            "version": settings.version,
            "docs": "/docs",
        }

    @app.get(
        "/health",
        response_model=HealthResponse,
        tags=["monitoring"],
        summary="Health Check",
    )
    async def health_check() -> HealthResponse:
        """
        Проверка состояния сервиса и зависимостей.

        Returns:
            Статус сервиса и всех зависимых сервисов.
        """
        # Проверяем Qdrant
        qdrant_health = await qdrant_client.health_check()

        # Определяем общий статус
        all_healthy = qdrant_health.get("status") == "healthy"
        overall_status = "healthy" if all_healthy else "degraded"

        return HealthResponse(
            status=overall_status,
            version=settings.version,
            services={
                "qdrant": ServiceHealth(
                    status=qdrant_health.get("status", "unknown"),
                    latency_ms=qdrant_health.get("latency_ms"),
                    error=qdrant_health.get("error"),
                ),
            },
        )

    return app


# =============================================================================
# Application Instance
# =============================================================================
app = create_application()
