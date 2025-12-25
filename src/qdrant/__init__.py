"""
Домен Qdrant.

API-интеграция с Qdrant векторной базой данных.

Структура домена:
    qdrant/
    ├── __init__.py      # Экспорт роутера (этот файл)
    ├── constants.py     # Константы и лимиты
    ├── schemas.py       # Pydantic DTOs
    ├── exceptions.py    # Доменные исключения
    ├── client.py        # Qdrant клиент (аналог repository)
    ├── service.py       # Бизнес-логика
    ├── router.py        # HTTP endpoints
    └── dependencies.py  # DI цепочка

Подключение в main.py:
    >>> from src.qdrant import router as qdrant_router
    >>> app.include_router(qdrant_router, prefix="/api/v1")
"""

from src.qdrant.router import router

__all__ = ["router"]
