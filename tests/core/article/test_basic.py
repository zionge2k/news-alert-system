import pytest

from tests.helpers import dummy_article_dto


def test_dummy_article_dto():
    article = dummy_article_dto()
    assert article.title.startswith("테스트 기사 제목")
    assert article.url.startswith("https://example.com/news/")
    assert article.author.endswith("기자")
    assert article.content.startswith("테스트 기사 내용입니다.")
    assert article.metadata.platform == "TEST"


def test_mock_article_collection(mock_article_collection):
    # 더미 기사 생성 및 insert
    article = dummy_article_dto().model_dump()
    import asyncio

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(mock_article_collection.insert_one(article))
    assert result.inserted_id.startswith("test_id_")
    # find_one 동작 확인
    found = loop.run_until_complete(
        mock_article_collection.find_one({"_id": result.inserted_id})
    )
    assert found["title"].startswith("테스트 기사 제목")
