"""
데이터베이스 모델 테스트를 위한 유틸리티 모듈입니다.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.article import ArticleModel, MongoArticleMetadata
from app.schemas.article import ArticleDTO, ArticleMetadata
from tests.helpers import dummy_article_dto


def create_mock_db_session():
    """
    데이터베이스 세션 모킹을 위한 컨텍스트 매니저를 생성합니다.

    Returns:
        데이터베이스 세션 모킹을 위한 패치 객체
    """
    return patch("motor.motor_asyncio.AsyncIOMotorClient")


def create_mock_article_model() -> ArticleModel:
    """
    테스트용 모의 ArticleModel 객체를 생성합니다.

    Returns:
        테스트용 ArticleModel 인스턴스
    """
    metadata = MongoArticleMetadata(
        platform="TEST",
        category="테스트",
        tags=["테스트", "단위테스트"],
        published_at=datetime.now(),
    )

    return ArticleModel(
        title="테스트 기사 제목",
        url="https://example.com/test",
        author="테스트 작성자",
        content="테스트 내용입니다.",
        metadata=metadata,
        unique_id="TEST_12345",
    )


async def insert_mock_articles(
    collection_mock, count: int = 3, platform: str = "TEST"
) -> List[Dict[str, Any]]:
    """
    모의 컬렉션에 지정된 수의 더미 기사를 추가합니다.

    Args:
        collection_mock: 모의 컬렉션 객체
        count: 추가할 기사 수
        platform: 기사 플랫폼

    Returns:
        추가된 기사 문서 목록
    """
    # 더미 ArticleDTO 객체 생성
    articles = []
    for i in range(count):
        article_dto = dummy_article_dto()
        # 플랫폼과 고유 ID 설정
        article_dto.metadata.platform = platform

        # ArticleModel로 변환
        article_model = ArticleModel.from_article_dto(article_dto)

        # 문서로 변환하여 저장
        article_doc = article_model.to_document()
        await collection_mock.insert_one(article_doc)

        articles.append(article_doc)

    return articles


def mock_mongodb_exception(method_name: str, exception: Exception):
    """
    특정 MongoDB 메서드에 대한 예외를 모킹합니다.

    Args:
        method_name: 예외를 발생시킬 메서드 이름 (예: "find_one", "insert_one")
        exception: 발생시킬 예외 객체

    Returns:
        패치 객체
    """
    return patch(
        f"motor.motor_asyncio.AsyncIOMotorCollection.{method_name}",
        side_effect=exception,
    )


def assert_article_fields_match(
    actual: Union[ArticleModel, Dict[str, Any]],
    expected: Union[ArticleDTO, Dict[str, Any]],
):
    """
    두 기사 객체(또는 딕셔너리)의 필드가 일치하는지 검증합니다.

    Args:
        actual: 실제 기사 객체 또는 딕셔너리
        expected: 예상 기사 객체 또는 딕셔너리
    """
    # 딕셔너리로 변환
    if isinstance(actual, ArticleModel):
        actual_dict = actual.to_document()
    else:
        actual_dict = actual

    if isinstance(expected, ArticleDTO):
        expected_dict = {
            "title": expected.title,
            "url": expected.url,
            "author": expected.author,
            "content": expected.content,
            "metadata": {
                "platform": expected.metadata.platform,
                "category": expected.metadata.category,
                "tags": expected.metadata.tags,
            },
        }
    else:
        expected_dict = expected

    # 주요 필드 비교
    assert actual_dict.get("title") == expected_dict.get(
        "title"
    ), "제목이 일치하지 않습니다."
    assert actual_dict.get("url") == expected_dict.get(
        "url"
    ), "URL이 일치하지 않습니다."
    assert actual_dict.get("author") == expected_dict.get(
        "author"
    ), "작성자가 일치하지 않습니다."

    # 메타데이터 비교
    actual_metadata = actual_dict.get("metadata", {})
    expected_metadata = expected_dict.get("metadata", {})

    assert actual_metadata.get("platform") == expected_metadata.get(
        "platform"
    ), "플랫폼이 일치하지 않습니다."
    assert actual_metadata.get("category") == expected_metadata.get(
        "category"
    ), "카테고리가 일치하지 않습니다."
