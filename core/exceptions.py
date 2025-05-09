from typing import Any, Dict, Optional


class DomainException(Exception):
    """
    도메인 계층의 모든 예외의 기본 클래스입니다.
    """

    def __init__(self, message: str, code: str = "domain_error"):
        self.message = message
        self.code = code
        super().__init__(message)


class EntityNotFoundException(DomainException):
    """
    엔티티를 찾을 수 없을 때 발생하는 예외입니다.
    """

    def __init__(self, entity_type: str, entity_id: Any):
        message = f"{entity_type} with id '{entity_id}' not found"
        super().__init__(message, code="entity_not_found")
        self.entity_type = entity_type
        self.entity_id = entity_id


class ValidationException(DomainException):
    """
    엔티티 유효성 검증에 실패했을 때 발생하는 예외입니다.
    """

    def __init__(self, message: str, errors: Optional[Dict[str, str]] = None):
        super().__init__(message, code="validation_error")
        self.errors = errors or {}


class AuthorizationException(DomainException):
    """
    권한이 없는 작업을 시도할 때 발생하는 예외입니다.
    """

    def __init__(
        self, message: str = "You don't have permission to perform this action"
    ):
        super().__init__(message, code="authorization_error")


class BusinessRuleViolationException(DomainException):
    """
    비즈니스 규칙을 위반했을 때 발생하는 예외입니다.
    """

    def __init__(self, message: str):
        super().__init__(message, code="business_rule_violation")
