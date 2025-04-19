# 데이터베이스 계층 (Database Layer)

이 디렉토리는 뉴스 알림 시스템의 데이터베이스 접근 계층을 구현합니다. MongoDB를 사용하여 뉴스 기사를 저장하고 검색하는 기능을 제공합니다.

## 디렉토리 구조

```
db/
├── repositories/              # 저장소 패턴 구현
│   ├── interfaces/            # 저장소 인터페이스 정의
│   │   ├── __init__.py
│   │   └── article_repository.py  # 기사 저장소 인터페이스
│   ├── __init__.py
│   └── article_repository.py  # MongoDB 저장소 구현
├── mongodb.py                 # MongoDB 연결 관리
└── README.md                  # 이 문서
```

## MongoDB 연결 관리 (mongodb.py)

`MongoDB` 클래스는 싱글톤 패턴을 사용하여 데이터베이스 연결을 관리합니다. 애플리케이션 수명 주기 동안 하나의 연결만 유지하도록 설계되었습니다.

### 주요 기능

1. **비동기 연결 설정**: `async def connect()` 메서드를 통해 MongoDB에 비동기 연결
2. **연결 종료**: `async def close()` 메서드로 연결 정리
3. **데이터베이스/컬렉션 접근**: `get_database()`, `get_collection()` 메서드를 통한 DB 접근
4. **에러 처리**: 연결 시 발생하는 오류를 적절히 처리하고 로깅

### 설정 방법

`.env` 파일을 통해 MongoDB 연결 정보를 구성할 수 있습니다:

```
MONGODB_URL=mongodb://root:1234@localhost:27017
MONGODB_DB_NAME=news_alert
```

### 사용 예시

```python
from db.mongodb import MongoDB, init_mongodb, close_mongodb

# 애플리케이션 시작 시 연결 초기화
await init_mongodb()

# DB 인스턴스 가져오기
db = MongoDB.get_database()

# 컬렉션 가져오기
articles_collection = MongoDB.get_collection("articles")

# 애플리케이션 종료 시 연결 종료
await close_mongodb()
```

## 저장소 패턴 (Repository Pattern)

`repositories/` 디렉토리는 저장소 패턴을 사용하여 데이터 액세스 로직을 비즈니스 로직과 분리합니다.

### BaseArticleRepository (인터페이스)

모든 기사 저장소 구현체가 준수해야 하는 인터페이스입니다.

```python
class BaseArticleRepository(ABC):
    @abstractmethod
    async def save_article(self, article: ArticleModel) -> Any:
        """기사를 저장소에 저장합니다."""
        pass
    
    @abstractmethod
    async def find_by_platform(self, platform: str) -> List[Dict[str, Any]]:
        """특정 플랫폼의 기사를 조회합니다."""
        pass
    
    @abstractmethod
    async def find_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """키워드가 포함된 기사를 조회합니다."""
        pass
    
    @abstractmethod
    async def find_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """URL로 기사를 조회합니다."""
        pass
    
    @abstractmethod
    async def find_by_unique_id(self, unique_id: str) -> Optional[Dict[str, Any]]:
        """복합키(unique_id)로 기사를 조회합니다."""
        pass
    
    @abstractmethod
    async def find_by_platform_and_article_id(self, platform: str, article_id: str) -> Optional[Dict[str, Any]]:
        """플랫폼과 기사ID 조합으로 기사를 조회합니다."""
        pass
```

### MongoArticleRepository (구현체)

MongoDB를 사용하여 기사 데이터를 저장하고 조회하는 저장소 구현체입니다.

```python
class MongoArticleRepository(BaseArticleRepository):
    collection_name = ArticleModel.collection_name
    
    async def save_article(self, article: ArticleModel) -> Any:
        """MongoDB에 기사를 저장하고 ObjectId를 반환합니다."""
        db = MongoDB.get_database()
        result = await db[self.collection_name].insert_one(article.model_dump())
        return result.inserted_id
    
    # 기타 메서드 구현...
```

### 싱글톤 인스턴스

이 프로젝트에서는 MongoArticleRepository의 싱글톤 인스턴스를 제공합니다:

```python
# 다음과 같이 미리 생성된 인스턴스를 임포트하여 사용
from db.repositories.article_repository import article_repository

# 사용 예시:
result = await article_repository.find_by_platform("YTN")
```

## 주요 기능

### 1. 기사 저장

```python
from app.models.article import ArticleModel
from app.schemas.article import ArticleDTO
from db.repositories.article_repository import article_repository

# ArticleDTO에서 ArticleModel로 변환
article_model = ArticleModel.from_article_dto(article_dto)

# 기사 저장
inserted_id = await article_repository.save_article(article_model)
```

### 2. 중복 기사 검사

```python
# 복합키 또는 URL로 중복 확인
unique_id = f"{platform}_{article_id}"
existing = await article_repository.find_by_unique_id(unique_id)

if not existing:
    # URL로 2차 중복 확인
    existing = await article_repository.find_by_url(article_url)
```

### 3. 키워드 기반 기사 검색

```python
# "코로나" 키워드가 포함된 기사 검색
articles = await article_repository.find_by_keyword("코로나")
```

### 4. 플랫폼별 기사 조회

```python
# YTN 뉴스 기사 조회
ytn_articles = await article_repository.find_by_platform("YTN")
```

## 주의사항

1. 모든 저장소 메서드는 비동기(`async`)로 구현되어 있으므로 항상 `await` 키워드로 호출해야 합니다.
2. MongoDB 객체 비교 시 `if db:` 대신 `if db is not None:` 사용해야 합니다.
3. MongoDB 컬렉션 이름은 ArticleModel 클래스에서 관리됩니다(`articles`).
4. 키워드 검색을 위해서는 MongoDB에 적절한 텍스트 인덱스가 생성되어 있어야 합니다.

## 에러 처리

데이터베이스 연결 실패 시 적절한 예외 처리와 로깅이 구현되어 있습니다:

```python
# DB가 연결되어 있는지 확인
if MongoDB.db is None:
    logger.error("MongoDB에 연결되어 있지 않습니다.")
    raise ConnectionError("MongoDB에 연결되어 있지 않습니다. connect() 메서드를 먼저 호출하세요.")
```

## 확장 방법

새로운 저장소 구현체를 추가하려면:

1. `interfaces/` 디렉토리에 적절한 인터페이스가 있는지 확인하고, 없으면 추가합니다.
2. 해당 인터페이스를 구현하는 새로운 저장소 클래스를 생성합니다.
3. 필요에 따라 싱글톤 인스턴스를 제공하여 일관된 사용성을 유지합니다. 