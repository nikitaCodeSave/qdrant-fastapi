"""
Базовые доменные исключения.

Иерархия исключений для всего приложения.
Домены наследуют от этих классов свои специфичные исключения.

Принцип: Service выбрасывает доменные исключения,
Router конвертирует их в HTTP ответы через exception_handler.

Example:
    >>> # В service.py
    >>> raise NotFoundError("Document not found", error_code="document_not_found")
    >>>
    >>> # В main.py exception_handler конвертирует в HTTP 404

Иерархия:
    DomainError (400) - базовый класс
    ├── NotFoundError (404)
    ├── AlreadyExistsError (409)
    ├── ValidationError (422)
    └── ConnectionError (503)
"""


class DomainError(Exception):
    """
    Базовое доменное исключение.

    Все бизнес-исключения наследуют от этого класса.
    Содержит информацию для формирования HTTP ответа.

    Attributes:
        message: Человекочитаемое описание ошибки.
        error_code: Машиночитаемый код для клиентов.
        status_code: HTTP статус код (по умолчанию 400).
        details: Дополнительные данные об ошибке.
    """

    message: str = "Domain error occurred"
    error_code: str = "domain_error"
    status_code: int = 400

    def __init__(
        self,
        message: str | None = None,
        error_code: str | None = None,
        details: dict | None = None,
    ) -> None:
        self.message = message or self.__class__.message
        self.error_code = error_code or self.__class__.error_code
        self.details = details
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Конвертация в dict для JSON ответа."""
        result = {
            "error": self.error_code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result


class NotFoundError(DomainError):
    """
    Ресурс не найден (HTTP 404).

    Example:
        >>> raise NotFoundError("Collection 'docs' not found")
    """

    message = "Resource not found"
    error_code = "not_found"
    status_code = 404


class AlreadyExistsError(DomainError):
    """
    Ресурс уже существует (HTTP 409 Conflict).

    Example:
        >>> raise AlreadyExistsError("Collection 'docs' already exists")
    """

    message = "Resource already exists"
    error_code = "already_exists"
    status_code = 409


class ValidationError(DomainError):
    """
    Ошибка валидации бизнес-правил (HTTP 422).

    Отличается от Pydantic ValidationError:
    это бизнес-валидация, не валидация схемы.

    Example:
        >>> raise ValidationError("Vector size must match collection config")
    """

    message = "Validation error"
    error_code = "validation_error"
    status_code = 422


class ConnectionError(DomainError):
    """
    Ошибка подключения к внешнему сервису (HTTP 503).

    Example:
        >>> raise ConnectionError("Cannot connect to Qdrant")
    """

    message = "Service connection error"
    error_code = "connection_error"
    status_code = 503
