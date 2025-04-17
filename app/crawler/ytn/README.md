# YTN 뉴스 API 문서

## API 엔드포인트

### 최신 뉴스 조회

```
POST https://www.ytn.co.kr/ajax/getManyNews.php
```

#### 요청 파라미터
- `mcd`: 카테고리 코드 (예: `total` - 전체 카테고리)

#### 요청 헤더
```python
{
    "Accept": "application/json, */*",                # JSON 응답 요청 (다른 형식도 허용)
    "Accept-Encoding": "gzip, deflate, br",          # 압축 지원
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7", # 한국어 우선
    "Cache-Control": "no-cache",                     # 캐시 비활성화
    "Connection": "keep-alive",                      # 연결 유지
    "Content-Type": "application/x-www-form-urlencoded", # POST 요청 데이터 형식
    "Referer": "https://www.ytn.co.kr/",            # 요청 출처
    "User-Agent": "<browser-user-agent>"            # fake_useragent로 생성
}
```

> 참고: 
> - 모든 헤더는 `app.crawler.utils.headers.create_ytn_headers()` 함수를 통해 자동 생성됩니다.
> - `User-Agent`는 fake_useragent 라이브러리를 통해 무작위로 생성됩니다.

#### 응답 헤더
```http
HTTP/2 200 
content-type: text/html; charset=UTF-8
content-length: 2158
date: Wed, 16 Apr 2025 05:51:08 GMT
server: Apache/2.4.6 (CentOS) OpenSSL/1.0.2k-fips
x-xss-protection: 1; mode=block
x-cache: Miss from cloudfront
via: 1.1 e1162a2a3f39fecec69b0ad3786d9cd8.cloudfront.net (CloudFront)
x-amz-cf-pop: ICN57-P5
x-amz-cf-id: zp-pfYkNEQAOfjpeiKbsTytltltvbnbaDhrdF6pApfCJaWCQxpGGgg==
X-Firefox-Spdy: h2
```

> 주의: 
> - YTN API는 `content-type: text/html`로 응답하지만, 실제 내용은 JSON 형식입니다.
> - 이 때문에 응답을 text로 받은 후 `sanitize_js_style_json` 함수를 통해 정리한 다음 JSON으로 파싱해야 합니다.
> - 아래 코드와 같이 처리합니다:
> ```python
> text_response = await response.text()
> cleaned_json = sanitize_js_style_json(text_response)
> data = json.loads(cleaned_json)
> ```

#### 응답 데이터 구조

```typescript
interface Article {
  title: string;     // 기사 제목
  mcd: string;       // 카테고리 코드 
  join_key: string;  // 기사 고유 ID (YYYYMMDDHHMMSS + 일련번호)
}
```

응답은 JSON 배열 형태로 제공됩니다:
```javascript
// 실제 응답 형식
Article[]
```

#### 응답 예시

```json
[
  {
    "title": "\"정치인 냄새가 난다\"...한덕수가 남긴 의미심장 편지 [Y녹취록]",
    "mcd": "0134",
    "join_key": "202504161240049780"
  },
  {
    "title": "\"생고기를 트럭 바닥에\"...경찰, 백종원 홍성바비큐축제 내사 착수",
    "mcd": "0103",
    "join_key": "202504161123263217"
  }
]
```

## 데이터 모델

### YtnArticleMetadata

YTN 뉴스의 메타데이터를 정의하는 Pydantic 모델입니다.

```python
class YtnArticleMetadata(ArticleMetadata):
    article_id: str           # 기사 고유 ID (join_key)
    category_code: str        # 카테고리 코드 (mcd)
```

### ArticleDTO[YtnArticleMetadata]

뉴스 기사 데이터를 표현하는 DTO 모델입니다.

```python
article_dto = ArticleDTO[YtnArticleMetadata](
    title="국민의힘 주자들 \"오세훈 잡아라\"...이재명·2김 공명선거 다짐",
    url="https://www.ytn.co.kr/_ln/0101_202504161142152344",
    content="",  # YTN API에서는 내용 요약을 제공하지 않음
    metadata=YtnArticleMetadata(
        platform="YTN",
        category="정치",
        article_id="202504161142152344",
        category_code="0101"
    )
)
```

## URL 구조

### 기사 URL 패턴
```
https://www.ytn.co.kr/_ln/[CATEGORY_CODE]_[JOIN_KEY]
```

- `[CATEGORY_CODE]`: 카테고리 코드 (예: 0101, 0103, 0134)
- `[JOIN_KEY]`: 기사 고유 ID (yyyyMMddHHmmss + 일련번호 형식)

## 카테고리 코드

| 코드   | 카테고리 |
|--------|----------|
| 0101   | 정치     |
| 0103   | 사회     |
| 0104   | 국제     |
| 0134   | 경제     |
| total  | 전체     |

## 참고사항

1. API 응답은 기사 제목과 ID만 제공하며, 본문 내용은 포함되지 않습니다.
2. 기사 본문을 얻으려면 URL 구조를 통해 웹페이지를 스크래핑해야 합니다.
3. `join_key`는 기사 게시 시간 정보를 포함하고 있습니다 (예: 202504161142152344는 2025년 4월 16일 11시 42분에 게시된 기사).

## 에러 처리

1. HTTP 상태 코드가 200이 아닌 경우 빈 리스트를 반환합니다.
2. 개별 기사 데이터 처리 중 오류가 발생하면 해당 기사는 건너뛰고 계속 진행합니다.
3. API 요청 자체가 실패하면 빈 리스트를 반환합니다. 