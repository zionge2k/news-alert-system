# JTBC 뉴스 API 문서

## API 엔드포인트

### 섹션별 기사 목록 조회

```
GET https://news-api.jtbc.co.kr/v1/get/contents/section/list/articles
```

#### 요청 파라미터
- `pageNo`: 페이지 번호 (필수, 기본값: 1)
- `pageSize`: 페이지 크기 (필수, 기본값: 10)
- `articleListType`: 기사 목록 유형 (필수, 기본값: "ARTICLE")
- `sectionIdx`: 섹션 인덱스 (선택, 예: 10 - 정치)

#### 응답 데이터 구조

```typescript
interface Article {
  articleIdx: string;                  // 기사 고유 ID (예: "NB12243049")
  articleTitle: string;                // 기사 제목
  articleMobileTitle: string | null;   // 모바일용 기사 제목
  articleInnerTextContent: string;     // 기사 내용
  rank: number | null;                 // 순위
  articleThumbnailImgUrl: string;      // 썸네일 이미지 URL
  articleThumbnailImageViewType: string; // 썸네일 이미지 뷰 타입
  isVideoView: boolean;                // 비디오 뷰 여부
  vodInfo: {                           // VOD 정보
    videoIdx: string;                  // 비디오 ID
    videoType: {                       // 비디오 타입
      code: string;                    // 코드
      name: string;                    // 이름
    };
    playTime: string;                  // 재생 시간
    vodThumbnailImgUrl: string | null; // VOD 썸네일 이미지 URL
  } | null;
  publicationDate: string;             // 발행일 (ISO 8601 형식)
  journalistName: string | null;       // 기자 이름
  isScrap: boolean;                    // 스크랩 여부
  readDate: string | null;             // 읽은 날짜
  expressionDate: string | null;       // 표현 날짜
  scrapDate: string | null;            // 스크랩 날짜
  bulletType: string | null;           // 불렛 타입
  isComment: boolean;                  // 댓글 여부
}

interface ArticlesResponse {
  resultCode: string;                  // 응답 코드
  resultMessage: string;               // 응답 메시지
  data: {
    currentPage: number;               // 현재 페이지
    pageSize: number;                  // 페이지 크기
    totalPages: number;                // 전체 페이지 수
    totalElements: number;             // 전체 요소 수
    list: Article[];                   // 기사 목록
  };
}
```

#### 응답 예시

```json
{
	"resultCode": "00",
	"resultMessage": "성공적으로 조회하였습니다.",
	"data": {
		"currentPage": 1,
		"pageSize": 10,
		"totalPages": 47958,
		"totalElements": 479573,
		"list": [
			{
				"articleIdx": "NB12243049",
				"articleTitle": "한미 협상카드 떠오른 '알래스카 LNG'…사업성 논란에 '신중론'",
				"articleMobileTitle": null,
				"articleInnerTextContent": "[앵커]\n\n상호 관세 문제를 놓고 우리 정부가 다음 주 미국과 본격 협상에 들어갑니다. 우리의 협상 카드로 거론되는 것 중 하나가 &#39;알래스카 가스관 개발 사업&#39;인데, 신중하게 접근해야 한다는 지적도 나옵니다.\n\n...",
				"rank": null,
				"articleThumbnailImgUrl": "https://thumb.jtbc.co.kr/photo/r600x0/news/cms/etc/2025/04/16/20250416193905600001.jpg",
				"articleThumbnailImageViewType": "WIDTH",
				"isVideoView": false,
				"vodInfo": {
					"videoIdx": "ND10696094",
					"videoType": {
						"code": "NORMAL",
						"name": "일반"
					},
					"playTime": "02:01",
					"vodThumbnailImgUrl": null
				},
				"publicationDate": "2025-04-16T19:37",
				"journalistName": null,
				"isScrap": false,
				"readDate": null,
				"expressionDate": null,
				"scrapDate": null,
				"bulletType": null,
				"isComment": false
			}
		]
	}
}
```

## 데이터 모델

### JtbcArticleMetadata

JTBC 뉴스의 메타데이터를 정의하는 Pydantic 모델입니다.

```python
class JtbcArticleMetadata(ArticleMetadata):
    article_id: str     # 기사 고유 ID (articleIdx)
    category: str       # 뉴스 카테고리 (섹션 이름)
    has_video: bool = False  # 비디오 포함 여부
    video_id: Optional[str] = None  # 비디오 ID (vodInfo.videoIdx)
```

### ArticleDTO[JtbcArticleMetadata]

뉴스 기사 데이터를 표현하는 DTO 모델입니다.

```python
article_dto = ArticleDTO[JtbcArticleMetadata](
    title="한미 협상카드 떠오른 '알래스카 LNG'…사업성 논란에 '신중론'",
    url="https://news.jtbc.co.kr/article/NB12243049",
    content="[앵커]\n\n상호 관세 문제를 놓고 우리 정부가 다음 주 미국과 본격 협상에...",
    author="김기자",  # 기자 이름이 있는 경우
    metadata=JtbcArticleMetadata(
        platform="JTBC",
        article_id="NB12243049",
        category="정치",
        has_video=True,  # 비디오가 있는 경우
        video_id="ND10696094",  # 비디오 ID
        collected_at=datetime.now(),
    )
)
```

## URL 구조

### 기사 URL 패턴
```
https://news.jtbc.co.kr/article/[ARTICLE_ID]
```

- `[ARTICLE_ID]`: 기사 고유 ID (예: "NB12243049")

## 섹션(카테고리) 코드

| 코드 | 카테고리 |
|------|----------|
| 10   | 정치     |
| 20   | 경제     |
| 30   | 사회     |
| 40   | 국제     |
| 50   | 문화     |
| 60   | 연예     |
| 70   | 스포츠   |
| 80   | 날씨     |

## 크롤링 프로세스

1. `CATEGORY_MAP`에 정의된 카테고리 코드와 이름을 사용합니다.
2. 각 카테고리별로 기사 목록 API를 호출하여 기사 정보를 수집합니다.
3. 각 기사에서 다음 정보를 추출합니다:
   - 기사 제목 (`articleTitle`)
   - 기사 ID (`articleIdx`)
   - 기사 내용 요약 (`articleInnerTextContent`)
   - 발행일 (`publicationDate`)
   - 기자 이름 (`journalistName`)
   - 비디오 정보 (`isVideoView`, `vodInfo.videoIdx`)
4. 수집된 모든 카테고리의 기사를 취합하여 반환합니다.

## 참고사항

1. 기사 목록 API는 페이지네이션을 지원합니다. 
   - 기본적으로 각 카테고리별로 첫 페이지만 조회합니다 (pageNo=1).
   - 각 페이지당 10개의 기사를 가져옵니다 (pageSize=10).
2. JTBC API 응답은 이미 JSON 형식으로 제공되므로 별도의 정제 과정이 필요하지 않습니다.
3. 기사 내용은 `articleInnerTextContent` 필드에서 일부 추출하여 요약으로 사용합니다.
4. 비디오 정보(`isVideoView` 및 `vodInfo`)는 메타데이터(`has_video`, `video_id`)로 저장됩니다.
5. 기자 이름(`journalistName`)은 ArticleDTO의 `author` 필드에 저장됩니다.

## 에러 처리

1. HTTP 상태 코드가 200이 아닌 경우 빈 리스트를 반환합니다.
2. 개별 기사 데이터 처리 중 오류가 발생하면 해당 기사는 건너뛰고 계속 진행합니다.
3. API 요청 자체가 실패하면 빈 리스트를 반환합니다.
4. 발행일 파싱에 실패한 경우 None으로 설정하고 계속 진행합니다. 