"""
Core 도메인 모듈 패키지입니다.
이 패키지는 애플리케이션의 핵심 비즈니스 로직을 담고 있습니다.
"""

from core.exceptions import (
    AuthorizationException,
    BusinessRuleViolationException,
    DomainException,
    EntityNotFoundException,
    ValidationException,
)
from core.interfaces import Repository, Service

# 개별 도메인 모듈 가져오기
# 필요에 따라 주석 해제하여 사용 가능
# from core.article import Article, ArticleService
# from core.queue import QueueItem, QueueService
# from core.published import PublishedArticle, PublishedService

__all__ = [
    # 공통 인터페이스
    "Repository",
    "Service",
    # 예외
    "DomainException",
    "EntityNotFoundException",
    "ValidationException",
    "AuthorizationException",
    "BusinessRuleViolationException",
    # 개별 도메인 모듈은 직접 import하여 사용
    # 'Article',
    # 'ArticleService',
    # 'QueueItem',
    # 'QueueService',
    # 'PublishedArticle',
    # 'PublishedService',
]
