# SBS 뉴스 크롤러

SBS 뉴스 웹사이트에서 최신 뉴스 기사를 수집하는 크롤러입니다.

## 개요

이 크롤러는 SBS 뉴스 검색 API를 사용하여 각 카테고리별 최신 뉴스를 비동기적으로 수집합니다. 수집된 기사는 표준화된 `ArticleDTO` 형식으로 변환되어 시스템의 다른 부분에서 일관되게 처리될 수 있습니다.

## 현재 상태

> **주의**: 현재 SBS 뉴스 API 엔드포인트에 접근할 수 없습니다. 웹사이트 구조나 API 엔드포인트가 변경되었을 가능성이 있습니다. 이 크롤러는 API 엔드포인트나 웹사이트 구조가 확인되면 업데이트가 필요합니다.

## API 엔드포인트

SBS 뉴스는 다음 검색 API 엔드포인트를 통해 뉴스 데이터를 제공할 것으로 예상됩니다:

```
https://news.sbs.co.kr/news/search/search_json.do
```

## 주요 카테고리

크롤러는 다음 카테고리의 뉴스를 수집합니다:

| 코드 | 카테고리 |
|------|----------|
| 01   | 정치     |
| 02   | 경제     |
| 03   | 사회     |
| 07   | 국제     |
| 08   | 문화/연예 |
| 09   | 스포츠   |

## 요청 파라미터

API 요청 시 다음 파라미터를 사용합니다:

- `keyword`: 검색 키워드 (빈 문자열로 설정하여 모든 뉴스 검색)
- `disp_cnt`: 표시할 기사 수 (예: "20")
- `sort`: 정렬 방식 (예: "date" - 날짜순)
- `catid`: 카테고리 코드 (예: "01", "02")
- `prddate_all`: 모든 날짜 포함 여부 (예: "y")

## 예상 응답 구조

API는 JSON 형식으로 응답하며, 주요 필드는 다음과 같습니다:

```json
{
  "SEARCH_RESULT": {
    "NEWS_LIST": [
      {
        "NEWS_ID": "기사 ID",
        "NEWS_TITLE": "기사 제목",
        "NEWS_SUMMARY": "기사 요약",
        "CATID": "카테고리 ID",
        "CATNAME": "카테고리 이름",
        "THUMB": "썸네일 이미지 URL",
        "NEWS_DATE": "발행 시간 (YYYY-MM-DD HH:MM:SS)"
      }
    ]
  }
}
```

## 사용 예시

```python
from app.crawler.sbs.api import SbsNewsApiCrawler

async def collect_sbs_news():
    crawler = SbsNewsApiCrawler()
    articles = await crawler.fetch_articles()
    
    print(f"SBS 뉴스 {len(articles)}건 수집 완료")
    
    # 수집된 기사 처리
    for article in articles:
        print(f"제목: {article.title}")
        print(f"URL: {article.url}")
        print(f"카테고리: {article.metadata.category}")
        print(f"발행시간: {article.metadata.published_at}")
        print("---")
```

## 문제 해결

현재 API 엔드포인트에 접근할 수 없는 경우, 다음과 같은 대안을 고려할 수 있습니다:

1. SBS 뉴스 웹사이트의 최신 구조 분석
2. 다른 API 엔드포인트 찾기
3. 웹 스크래핑 방식으로 전환 (HTML 파싱)
4. SBS 뉴스 RSS 피드 활용 (사용 가능한 경우)

## 에러 처리

크롤러는 다음과 같은 예외 상황을 처리합니다:

- HTTP 요청 실패
- JSON 파싱 오류
- 필수 필드 누락
- 날짜 형식 파싱 오류

모든 예외는 로깅되며, 가능한 경우 다음 카테고리 처리를 계속합니다. 