# 코드베이스 구조 분석

## 1. 프로젝트 개요

News Alert System은 여러 언론사의 뉴스를 크롤링하고 분석하여 디스코드를 통해 알림을 제공하는 시스템입니다. 이 시스템은 Python 3.11 이상 환경에서 실행되며, 의존성 관리를 위해 Poetry를 사용합니다. 

### 주요 기능:
- 비동기 크롤링: `aiohttp` + `BeautifulSoup4`를 이용하여 YTN, MBC, JTBC 등 주요 언론사의 뉴스를 크롤링
- MongoDB 저장: 수집된 뉴스 기사를 효율적으로 저장하고 관리
- 알림 전송: Discord를 통한 알림 전송
- 확장성: 새로운 뉴스 소스를 쉽게 추가할 수 있는 구조

## 2. 디렉토리 구조

```
news-alert-system/
├── app/                    # 핵심 애플리케이션 코드
│   ├── crawler/            # 비동기 뉴스 크롤러
│   │   ├── ytn/            # YTN 뉴스 크롤러
│   │   ├── mbc/            # MBC 뉴스 크롤러 
│   │   ├── jtbc/           # JTBC 뉴스 크롤러
│   │   ├── registry.py     # 크롤러 레지스트리
│   │   └── base.py         # 기본 크롤러 인터페이스
│   ├── models/             # DB 모델 정의
│   ├── schemas/            # Pydantic 스키마
│   ├── storage/            # 저장소 관련 코드
│   └── publisher/          # Discord 알림 모듈
│
├── db/                     # 데이터베이스 관련 코드
│
├── common/                 # 공통 유틸리티
│   └── utils/              # 유틸리티 함수
│
├── scripts/                # 실행 스크립트
│
├── tests/                  # 테스트 코드
├── pipelines/              # 데이터 처리 파이프라인
│   └── discord_publisher/  # Discord 알림 파이프라인
│
├── pyproject.toml          # Poetry 의존성 관리
├── .gitignore              # Git 설정
├── docker-compose.yml      # Docker Compose 설정
└── README.md               # 프로젝트 README
```

## 3. 핵심 모듈 분석

### 3.1 app/crawler

뉴스 크롤링을 담당하는 모듈입니다. 모든 크롤러는 `BaseNewsCrawler` 추상 클래스를 상속받아 구현됩니다.

- **base.py**: 크롤러의 기본 인터페이스를 정의합니다. `fetch_articles()` 추상 메서드를 포함합니다.
- **registry.py**: 모든 크롤러를 등록하는 레지스트리입니다. 새로운 크롤러를 추가할 때 이 파일에 등록합니다.
- **언론사별 디렉토리 (ytn/, mbc/, jtbc/)**:
  - 각 언론사별 크롤러 구현이 포함됩니다.
  - 각 디렉토리에는 `api.py`가 있어 해당 언론사 API를 이용한 크롤링 로직이 구현되어 있습니다.

### 3.2 app/schemas

데이터 유효성 검사 및 직렬화를 위한 Pydantic 모델들이 있습니다.

- **article.py**:
  - `ArticleMetadata`: 뉴스 메타데이터 기본 모델
  - `ArticleDTO`: 뉴스 기사 데이터 전송 객체 (제네릭 타입 사용)

### 3.3 app/models

MongoDB 문서 모델을 정의합니다.

- **article.py**:
  - `MongoArticleMetadata`: MongoDB에 저장될 메타데이터 모델
  - `ArticleModel`: MongoDB에 저장될 기사 문서 모델
  - `create_article_indexes()`: 인덱스 생성 함수

### 3.4 app/storage

데이터 저장 관련 코드입니다.

- **queue/**: 작업 큐 관련 코드
- **published/**: 발행된 기사 저장 관련 코드

### 3.5 app/publisher

알림 전송을 담당하는 모듈입니다.

- **discord/**: Discord를 통한 알림 전송 기능 구현

## 4. 의존성 관계

```
app/schemas/article.py (데이터 정의)
        ↑
app/crawler/base.py (크롤러 인터페이스)
        ↑
app/crawler/{source}/api.py (구체적인 크롤러 구현)
        ↑
app/crawler/registry.py (크롤러 등록)
        ↓
app/models/article.py (MongoDB 문서 모델)
        ↓
app/storage/ (데이터 저장)
        ↓
app/publisher/ (알림 전송)
```

## 5. 의존성 패키지

프로젝트는 다음 주요 의존성 패키지를 사용합니다:

- **aiohttp**: 비동기 HTTP 요청 처리
- **beautifulsoup4**: HTML 파싱
- **python-dotenv**: 환경 변수 관리
- **fake-useragent**: 웹 크롤링 시 User-Agent 관리
- **pydantic**: 데이터 검증 및 설정 관리
- **motor**: 비동기 MongoDB 드라이버
- **discord-py**: Discord 봇 API 사용
- **pydantic-settings**: 설정 관리

개발 의존성:
- **pre-commit**: Git hook 관리
- **black**: 코드 포매팅
- **isort**: 임포트 정렬

## 6. 확장성 및 테스트 가능성

### 확장성

1. **크롤러 추가**: `BaseNewsCrawler`를 상속받아 새로운 크롤러를 구현하고 `registry.py`에 등록하면 새 언론사를 쉽게 추가할 수 있습니다.
2. **메타데이터 확장**: `ArticleMetadata`를 상속받아 언론사별 특수 메타데이터를 정의할 수 있습니다.
3. **파이프라인 확장**: 새로운 알림 채널이나 데이터 처리 단계를 추가할 수 있습니다.

### 테스트 가능성

1. **의존성 주입**: 추상 클래스와 인터페이스 사용으로 모의 객체(mock) 생성이 용이합니다.
2. **모듈 분리**: 기능별 모듈 분리로 단위 테스트가 용이합니다.
3. **비동기 코드**: 비동기 코드 테스트를 위한 특별한 접근이 필요합니다.

## 7. 개선 가능한 영역

1. **테스트 부족**: 현재 테스트 코드가 충분하지 않습니다. 단위 테스트 및 통합 테스트를 추가해야 합니다.
2. **문서화**: 일부 모듈과 클래스에 대한 자세한 문서화가 필요합니다.
3. **설정 관리**: 환경 변수 및 설정 관리가 명확하지 않습니다.
4. **예외 처리**: 크롤링 중 발생할 수 있는 예외 처리 강화가 필요합니다.
5. **로깅**: 체계적인 로깅 시스템 구축이 필요합니다.

## 8. 결론

News Alert System은 모듈화가 잘 되어 있고 확장성이 높은 구조를 가지고 있습니다. 새로운 뉴스 소스와 알림 채널을 쉽게 추가할 수 있어 다양한 용도로 확장 가능합니다.

테스트 환경 구성 시에는 비동기 코드 테스트를 위한 특별한 접근이 필요하며, 단위 테스트와 통합 테스트를 균형 있게 구성해야 합니다. 