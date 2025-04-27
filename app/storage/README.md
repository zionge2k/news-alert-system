# 뉴스 알림 큐 시스템

이 디렉토리는 뉴스 기사를 Discord로 발행하기 전에 중간 버퍼 역할을 하는 큐 시스템을 구현합니다.

## 주요 기능

- MongoDB를 사용한 큐 시스템
- 중복 기사 필터링
- 상태 관리 (대기, 처리중, 완료, 실패)
- 실패 처리 및 재시도 메커니즘
- MongoDB에 저장된 기사를 큐에 추가하는 기능

## 데이터 흐름

모든 뉴스 기사는 MongoDB에 먼저 저장된 후에 큐에 추가되어야 합니다:

```
크롤링 -> [ArticleDTO] -> [ArticleModel] -> DB 저장 -> [QueueItem] -> 발행
```

## 구조

```
storage/
└── queue/
    ├── __init__.py         # 패키지 초기화
    ├── interfaces.py       # 큐 인터페이스 정의
    ├── mongodb_queue.py    # MongoDB 구현체
    └── services.py         # 서비스 계층
```

## 사용 방법

### 1. MongoDB에 저장된 기사를 큐에 추가하기

```python
from storage.queue.services import queue_service

# MongoDB에서 기사 가져와 추가 (JTBC 뉴스, 정치 카테고리, 최근 24시간)
await queue_service.add_articles_from_db(
    platform="JTBC",
    category="정치",
    limit=50,
    hours=24
)

# 모든 플랫폼, 모든 카테고리, 최근 12시간 기사 추가
await queue_service.add_articles_from_db(
    hours=12
)
```

### 2. 큐에서 처리할 기사 가져오기

```python
# 최대 10개 기사 가져오기
articles = await queue_service.get_pending_articles(limit=10)

for article in articles:
    try:
        # 기사 발행 처리 (Discord에 전송)
        # ...

        # 성공적으로 처리된 경우
        await queue_service.mark_article_published(article.unique_id)
    except Exception as e:
        # 실패한 경우
        await queue_service.mark_article_failed(
            article.unique_id, 
            error_message=str(e)
        )
```

### 3. 실패한 기사 재시도하기

```python
# 최대 3번까지 실패한 기사 재시도
retry_count = await queue_service.retry_failed_articles(max_retries=3)
```

### 4. 큐 상태 조회하기

```python
# 상태별 기사 수 조회
status = await queue_service.get_queue_status()
print(f"대기 중: {status.get('pending', 0)}개")
print(f"처리 중: {status.get('processing', 0)}개")
print(f"완료: {status.get('completed', 0)}개")
print(f"실패: {status.get('failed', 0)}개")
```

### 5. 오래된 완료 기사 정리하기

```python
# 7일 이상 지난 완료 기사 정리
cleaned_count = await queue_service.clean_old_articles(days=7)
```

## 테스트

큐 시스템 테스트를 위해 `scripts/test_queue.py` 스크립트를 사용할 수 있습니다.

```bash
# 큐 상태 확인
python scripts/test_queue.py --action status

# 실패 항목 재시도
python scripts/test_queue.py --action retry --max-retries 3

# 오래된 항목 정리
python scripts/test_queue.py --action clean --days 7

# MongoDB에서 기사 가져와 큐에 추가
python scripts/test_queue.py --action add --platform YTN --category 정치 --hours 12 --limit 20
``` 