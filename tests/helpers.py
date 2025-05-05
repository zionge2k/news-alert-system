"""
테스트를 위한 공통 헬퍼 함수와 유틸리티를 제공하는 모듈입니다.
"""

import json
import os
import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from app.schemas.article import ArticleDTO, ArticleMetadata


def random_string(length: int = 10) -> str:
    """
    지정된 길이의 랜덤 문자열을 생성합니다.

    Args:
        length: 생성할 문자열의 길이 (기본값: 10)

    Returns:
        생성된 랜덤 문자열
    """
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def random_datetime(days_ago: int = 30, future: bool = False) -> datetime:
    """
    현재 기준으로 랜덤한 날짜시간을 생성합니다.

    Args:
        days_ago: 몇 일 전까지의 범위에서 생성할지 (기본값: 30)
        future: 미래 날짜를 포함할지 여부 (기본값: False)

    Returns:
        랜덤하게 생성된 datetime 객체
    """
    now = datetime.now()
    delta = random.randint(0, days_ago)

    if future:
        delta = delta * random.choice([-1, 1])

    return now + timedelta(days=delta)


def dummy_article_metadata(
    platform: str = "TEST",
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    published_at: Optional[datetime] = None,
) -> ArticleMetadata:
    """
    테스트용 더미 ArticleMetadata 객체를 생성합니다.

    Args:
        platform: 뉴스 플랫폼 이름 (기본값: "TEST")
        category: 뉴스 카테고리 (기본값: None - 랜덤 생성)
        tags: 태그 목록 (기본값: None - 랜덤 생성)
        published_at: 발행 시간 (기본값: None - 랜덤 생성)

    Returns:
        생성된 ArticleMetadata 객체
    """
    if category is None:
        categories = ["정치", "경제", "사회", "문화", "국제", "스포츠", "기술"]
        category = random.choice(categories)

    if tags is None:
        all_tags = [
            "뉴스",
            "속보",
            "단독",
            "정부",
            "기업",
            "사건",
            "사고",
            "정책",
            "국회",
            "투자",
        ]
        tags = random.sample(all_tags, k=random.randint(1, 4))

    if published_at is None:
        published_at = random_datetime()

    return ArticleMetadata(
        platform=platform, category=category, tags=tags, published_at=published_at
    )


def dummy_article_dto(
    title: Optional[str] = None,
    url: Optional[str] = None,
    author: Optional[str] = None,
    content: Optional[str] = None,
    metadata: Optional[ArticleMetadata] = None,
) -> ArticleDTO:
    """
    테스트용 더미 ArticleDTO 객체를 생성합니다.

    Args:
        title: 기사 제목 (기본값: None - 랜덤 생성)
        url: 기사 URL (기본값: None - 랜덤 생성)
        author: 기자 이름 (기본값: None - 랜덤 생성)
        content: 기사 내용 (기본값: None - 랜덤 생성)
        metadata: 메타데이터 (기본값: None - 랜덤 생성)

    Returns:
        생성된 ArticleDTO 객체
    """
    if title is None:
        title = f"테스트 기사 제목 {random_string(5)}"

    if url is None:
        url = f"https://example.com/news/{random_string(8)}"

    if author is None:
        author = f"{random.choice(['김', '이', '박', '최', '정'])}기자"

    if content is None:
        content = f"테스트 기사 내용입니다. {random_string(50)}"

    if metadata is None:
        metadata = dummy_article_metadata()

    return ArticleDTO(
        title=title, url=url, author=author, content=content, metadata=metadata
    )


def load_test_data(file_name: str) -> Dict[str, Any]:
    """
    테스트 데이터 파일을 로드합니다.

    Args:
        file_name: 로드할 파일 이름 (tests/data/ 디렉토리 내의 파일)

    Returns:
        로드된 데이터 (보통 딕셔너리)

    Raises:
        FileNotFoundError: 파일을 찾을 수 없는 경우
    """
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    file_path = os.path.join(data_dir, file_name)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"테스트 데이터 파일을 찾을 수 없습니다: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_test_data_file(data: Dict[str, Any], file_name: str) -> str:
    """
    테스트 데이터를 파일로 저장합니다.

    Args:
        data: 저장할 데이터
        file_name: 저장할 파일 이름

    Returns:
        저장된 파일의 경로
    """
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)

    file_path = os.path.join(data_dir, file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return file_path
