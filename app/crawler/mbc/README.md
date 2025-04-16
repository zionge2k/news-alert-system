# MBC 뉴스 API 문서

## API 엔드포인트

### 헤드라인 뉴스 조회

```
GET https://imnews.imbc.com/operate/common/main/topnews/headline_news.js
```

#### 요청 파라미터
- 타임스탬프 (선택): `?YYYYMMDDHHMM=` 형식 (예: `?202504161301=`)

#### 요청 헤더
```python
{
    "Accept": "application/json, */*",                # JSON 응답 요청 (다른 형식도 허용)
    "Accept-Encoding": "gzip, deflate, br",          # 압축 지원
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7", # 한국어 우선
    "Cache-Control": "no-cache",                     # 캐시 비활성화
    "Connection": "keep-alive",                      # 연결 유지
    "Referer": "https://imnews.imbc.com/",          # 요청 출처
    "User-Agent": "<browser-user-agent>"            # fake_useragent로 생성
}
```

> 참고: 
> - 모든 헤더는 `app.crawler.utils.headers.create_mbc_headers()` 함수를 통해 자동 생성됩니다.
> - `User-Agent`는 fake_useragent 라이브러리를 통해 무작위로 생성됩니다.

#### 응답 헤더
```http
HTTP/2 200
content-type: application/javascript; charset=utf-8
vary: Accept-Encoding
access-control-allow-origin: *
content-encoding: gzip
server: NCE
x-nce-cacheresult: HIT
```

#### 응답 데이터 구조

```typescript
interface Article {
  Section: string;    // 뉴스 섹션 (예: "정치", "경제")
  AId: string;        // 기사 고유 ID
  Title: string;      // 기사 제목
  Desc: string;       // 기사 설명/요약
  Image: string;      // 썸네일 이미지 URL (상대 경로)
  Link: string;       // 기사 전문 URL
  IsVod: "Y" | "N";  // 동영상 포함 여부
}
```

응답은 일반 JSON이 아닌 JavaScript 변수 할당문 형태로 제공됩니다:
```javascript
// 실제 응답 형식
var newsData = {
  "Data": Article[]
};
```

> 참고: 
> - 응답이 `var newsData = {...};` 형태로 오기 때문에 바로 JSON 파싱이 불가능합니다.
> - 파싱하기 전에 `sanitize_js_style_json` 함수로 JavaScript 코드를 JSON 형식으로 변환해야 합니다.

#### 응답 예시

```json
{
  "Data": [
    {
      "Section": "정치",
      "AId": "6706959",
      "Title": "與 \"대통령 거부권 행사는 정당\"... 野 \"독재 수준 폭거\"",
      "Desc": "여야가 대통령의 '검수완박 2법' 거부권 행사를 두고...",
      "Image": "//image.imnews.imbc.com/news/2024/politics/article/6706959_1.jpg",
      "Link": "https://imnews.imbc.com/news/2024/politics/article/6706959_36711.html",
      "IsVod": "N"
    }
  ]
}
```

## 데이터 모델

### MbcArticleMetadata

MBC 뉴스의 메타데이터를 정의하는 Pydantic 모델입니다.

```python
class MbcArticleMetadata(ArticleMetadata):
    article_id: str           # 기사 고유 ID
    is_video: bool = False    # 동영상 포함 여부
    image_url: str | None = None  # 이미지 URL (정규화된 절대 경로)
```

### ArticleDTO[MbcArticleMetadata]

뉴스 기사 데이터를 표현하는 DTO 모델입니다.

```python
article_dto = ArticleDTO[MbcArticleMetadata](
    title="뉴스 제목",
    url="https://imnews.imbc.com/...",
    content="기사 설명",
    metadata=MbcArticleMetadata(
        platform="MBC",
        category="사회",
        article_id="6706959",
        is_video=False,
        image_url="https://image.imnews.imbc.com/..."
    )
)
```

## URL 구조

### 기사 URL 패턴
```
https://imnews.imbc.com/news/[YEAR]/[SECTION]/article/[ARTICLE_ID]_[CATEGORY_ID].html
```

- `[YEAR]`: 연도 (예: 2024)
- `[SECTION]`: 섹션명 (예: politics, econo, society, world)
- `[ARTICLE_ID]`: 기사 고유 ID
- `[CATEGORY_ID]`: 카테고리 ID (예: 36711)

## 참고사항

1. 이미지 URL은 상대 경로(`//`)로 제공되며, 크롤러에서 `https:`를 추가하여 절대 경로로 변환합니다.
   - 예: `//image.imnews.imbc.com/...` → `https://image.imnews.imbc.com/...`
   - 주의: 이미지 서버의 CORS 정책이나 접근 제한으로 인해 직접 요청이 실패할 수 있습니다.
2. `IsVod` 필드가 "Y"인 경우 `is_video` 메타데이터가 `True`로 설정됩니다.
3. 모든 API 응답 필드는 문자열(string) 타입으로 제공됩니다.
4. 응답 데이터는 JavaScript 형식으로 제공되므로 `sanitize_js_style_json` 유틸리티를 사용하여 정리 후 파싱합니다.

## 에러 처리

1. HTTP 상태 코드가 200이 아닌 경우 빈 리스트를 반환합니다.
2. 개별 기사 데이터 처리 중 오류가 발생하면 해당 기사는 건너뛰고 계속 진행합니다.
3. API 요청 자체가 실패하면 빈 리스트를 반환합니다. 