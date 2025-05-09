import pytest
from bs4 import BeautifulSoup


# 예시 JTBC 크롤러 (실제 구현체 import 경로에 맞게 수정 필요)
class JTBCNewsCrawler:
    def parse(self, html):
        soup = BeautifulSoup(html, "html.parser")
        title = soup.select_one(".title").text
        content = soup.select_one(".content").text
        source = soup.select_one(".source").text
        published_at = soup.select_one("time")["datetime"]
        return {
            "title": title,
            "content": content,
            "source": source,
            "published_at": published_at,
        }


def test_jtbc_crawler_parsing():
    with open("tests/services/crawler/sample_html/jtbc.html", encoding="utf-8") as f:
        html = f.read()
    crawler = JTBCNewsCrawler()
    news = crawler.parse(html)
    assert news["title"] == "테스트 뉴스 제목"
    assert news["content"] == "테스트 본문 내용"
    assert news["source"] == "JTBC"
    assert news["published_at"] == "2024-06-01T12:00:00Z"


def test_jtbc_crawler_missing_element():
    html = "<html><body><div class='news'></div></body></html>"
    crawler = JTBCNewsCrawler()
    with pytest.raises(AttributeError):
        crawler.parse(html)
