# 뉴스 알림 시스템 인프라 계층 문서

이 문서는 뉴스 알림 시스템의 인프라 계층에 대한 설명과 사용 방법을 제공합니다.

## 개요

인프라 계층은 외부 서비스 및 데이터 저장소와의 통신을 담당하는 재사용 가능한 컴포넌트를 제공합니다. 이 계층은 다음과 같은 모듈로 구성됩니다:

- **데이터베이스**: MongoDB와 같은 데이터베이스에 대한 추상화 및 구현체
- **HTTP 클라이언트**: 외부 API와의 통신을 위한 클라이언트
- **메시징 클라이언트**: Discord와 같은 메시징 서비스와의 통신을 위한 클라이언트

## 구조

인프라 계층은 다음과 같은 구조로 구성되어 있습니다:

```
infra/
├── __init__.py               # 주요 컴포넌트 내보내기
├── database/                 # 데이터베이스 관련 코드
│   ├── __init__.py           # 데이터베이스 모듈 내보내기
│   ├── base.py               # 데이터베이스 인터페이스
│   ├── mongodb.py            # MongoDB 구현체
│   └── repository/           # 저장소 패턴 구현
│       ├── __init__.py       # 저장소 모듈 내보내기
│       ├── article.py        # 아티클 저장소 인터페이스
│       ├── factory.py        # 저장소 팩토리
│       └── mongodb/          # MongoDB 저장소 구현체
│           ├── __init__.py   # MongoDB 저장소 내보내기
│           └── article.py    # MongoDB 아티클 저장소
├── clients/                  # 외부 서비스 클라이언트
│   ├── __init__.py           # 클라이언트 내보내기
│   ├── http.py               # HTTP 클라이언트
│   └── messaging.py          # 메시징 클라이언트
```

## 주요 컴포넌트 및 사용 방법

### 데이터베이스

#### MongoDB 연결

MongoDB 연결을 설정하려면 다음과 같이 합니다:

```python
from infra.database import create_mongodb_connection

# 기본 환경 변수 사용하여 MongoDB 연결 생성
mongodb = create_mongodb_connection()

# 명시적으로 URL과 DB 이름 지정
mongodb = create_mongodb_connection(
    uri="mongodb://localhost:27017",
    database="news_alert"
)

# 연결 및 초기화
await mongodb.connect()

# 작업 수행...

# 연결 종료
await mongodb.disconnect()
```

#### 저장소 패턴 사용

데이터 저장소에 접근하기 위해 저장소 패턴을 사용합니다:

```python
from infra.database import create_mongodb_connection, create_article_repository, ArticleModel

# MongoDB 연결 생성
mongodb = create_mongodb_connection()
await mongodb.connect()

# 아티클 저장소 생성
article_repo = create_article_repository(mongodb)

# 아티클 생성
article = ArticleModel(
    url="https://example.com/news/1",
    title="새로운 뉴스 제목",
    content="뉴스 내용...",
    unique_id="news_1",
    metadata={"source": "example.com"}
)

# 저장
await article_repo.save(article)

# 조회
retrieved = await article_repo.find_by_id(article.id)
articles = await article_repo.find_all()
```

### HTTP 클라이언트

외부 API와 통신하기 위한 HTTP 클라이언트:

```python
from infra.clients.http import AioHttpClient

# 클라이언트 생성
http_client = AioHttpClient(
    base_url="https://api.example.com",
    timeout=30,
    default_headers={"User-Agent": "NewsAlertSystem/1.0"}
)

# GET 요청
response = await http_client.get("/news?category=tech")

# POST 요청
data = {"title": "뉴스 제목", "content": "뉴스 내용"}
response = await http_client.post("/news", json_data=data)

# 세션 종료
await http_client.close()
```

### 메시징 클라이언트

Discord와 같은 메시징 서비스와 통신하기 위한 클라이언트:

```python
from infra.clients.messaging import DiscordClient, Message

# Discord 클라이언트 생성
discord = DiscordClient(webhook_url="https://discord.com/api/webhooks/...")

# 메시지 전송
message = Message(
    title="새로운 뉴스 알림",
    content="중요한 뉴스가 발생했습니다!",
    url="https://example.com/news/1"
)
await discord.send_message(message)
```

## 레거시 코드와의 호환성

기존 코드가 새로운 인프라 계층으로 마이그레이션하는 동안 어댑터를 통해 호환성을 유지할 수 있습니다:

```python
# 레거시 방식
from adapters.infra import MongoDBAdapter, init_mongodb

# 기존 방식으로 MongoDB 초기화
await init_mongodb()

# 어댑터 인스턴스 가져오기
mongodb = MongoDBAdapter.get_instance()
db = mongodb.get_database()

# HTTP 클라이언트 어댑터 사용
from adapters.infra import HTTPClientAdapter

http_client = HTTPClientAdapter(base_url="https://api.example.com")
response = await http_client.get("/news/1")
```

## 권장 사항

- 새로운 코드는 직접 `infra` 패키지를 사용하는 것을 권장합니다.
- 레거시 코드는 점진적으로 `adapters` 패키지에서 직접 `infra` 패키지로 마이그레이션하세요.
- 어댑터를 사용할 때 `DeprecationWarning`이 표시되며, 이는 코드를 마이그레이션해야 한다는 신호입니다.

## 모범 사례

1. **리소스 관리**: 항상 `async with` 구문이나 명시적인 `close()` 호출을 통해 연결을 관리하세요.
2. **의존성 주입**: 직접 인스턴스를 생성하지 말고 의존성 주입을 통해 컴포넌트를 전달하세요.
3. **비동기 처리**: 모든 I/O 작업은 `async`/`await` 구문을 사용하여 비동기적으로 처리하세요.
4. **에러 처리**: 항상 적절한 예외 처리를 통해 외부 서비스 실패에 대응하세요.

## 예외 처리

인프라 계층은 다음과 같은 예외를 발생시킬 수 있습니다:

- `ConnectionError`: 연결 문제 발생시
- `TimeoutError`: 요청 시간 초과시
- `ValueError`: 잘못된 파라미터 제공시

모든 데이터베이스 예외는 `infra.database.DatabaseError`로 래핑되어 있으며, HTTP 요청 예외는 `infra.clients.http.HttpError`로 래핑되어 있습니다.

## 테스트

인프라 컴포넌트를 테스트할 때는 모의(mock) 객체를 사용하여 외부 의존성을 격리하세요:

```python
from unittest.mock import patch, AsyncMock

# HTTP 클라이언트 모킹
with patch('infra.clients.http.AioHttpClient.get') as mock_get:
    mock_get.return_value = {"status": "ok", "data": {...}}
    
    # 테스트 코드...
``` 