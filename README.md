# 🔍 실시간 뉴스 수집/분석/알림 시스템

## 소개

이 프로젝트는 여러 언론사의 뉴스 웹사이트를 비동기 방식으로 크롤링하고, 텍스트 전처리 및 키워드 분석을 거쳐 특정 키워드(예: 주식, 경제, 사건 등)를 포함한 뉴스에 대해 discord 알림을 전송하는 시스템입니다.

> ⚙️ 이 프로젝트는 **Python 3.11 이상**, **Poetry**를 사용하여 의존성을 관리하며, **Docker Compose**를 기반으로 누구나 동일한 환경에서 실행할 수 있도록 설계되었습니다.

## 주요 기능

- ✅ **비동기 크롤링**: `aiohttp` + `BeautifulSoup4`
- ✅ **뉴스 API 통합**: YTN, MBC, JTBC 등 주요 언론사 API 크롤링
- ✅ **MongoDB 저장**: 수집된 뉴스 기사의 효율적인 저장 및 관리
- ✅ **작업 큐 처리**: `Redis` 또는 `RabbitMQ`
- ✅ **분석 및 전처리**: 키워드 기반 텍스트 분석
- ✅ **알림 전송**: discord 연동
- ✅ **결과 API 제공**: `FastAPI`
- ✅ **뉴스 저장**: `MongoDB`

## 프로젝트 구조

```bash
news-alert-system/
├── app/                    # 핵심 애플리케이션 코드
│   ├── crawler/            # 비동기 뉴스 크롤러
│   │   ├── ytn/            # YTN 뉴스 크롤러
│   │   ├── mbc/            # MBC 뉴스 크롤러 
│   │   ├── jtbc/           # JTBC 뉴스 크롤러
│   │   ├── registry.py     # 크롤러 레지스트리
│   │   └── base.py         # 기본 크롤러 인터페이스
│   ├── processor/          # 텍스트 전처리 및 키워드 분석
│   ├── notifier/           # Slack 알림 모듈
│   ├── api/                # FastAPI 엔드포인트
│   ├── models/             # DB 모델 정의
│   └── schemas/            # Pydantic 스키마
│
├── db/                     # 데이터베이스 관련 코드
│   ├── repositories/       # 저장소 패턴 구현
│   └── mongodb.py          # MongoDB 연결 관리
│
├── common/                 # 공통 유틸리티
│   └── utils/              # 유틸리티 함수
│       └── logger.py       # 로깅 유틸리티
│
├── scripts/                # 실행 스크립트
│   ├── run_all.py          # 전체 크롤링 및 저장 실행
│   └── count_documents.py  # 문서 수 확인 스크립트
│
├── tests/                  # 테스트 코드
├── Dockerfile              # 서비스용 Dockerfile
├── docker-compose.yml      # 전체 서비스 오케스트레이션
├── pyproject.toml          # Poetry 의존성 관리
└── README.md               # 이 문서
```

## 실행 방법

### 1. Docker 기반 실행 (권장)

```bash
docker-compose up --build
```

- 이 명령어 하나로 Redis/PostgreSQL/MongoDB 등 필요한 모든 서비스가 함께 실행됩니다.
- 이후 `http://localhost:8000/docs`에서 API 문서를 확인할 수 있습니다.

### 2. 개발 환경 설정 (Poetry)

```bash
poetry install
poetry shell
```

> `.env` 파일 등 필요한 환경변수는 추후 `env.example`로 제공 예정입니다.

### 3. 크롤링 실행 및 데이터 확인

모든 뉴스 크롤러를 실행하고 MongoDB에 저장:

```bash
python scripts/run_all.py
```

MongoDB에 저장된 뉴스 기사 수 확인:

```bash
python scripts/count_documents.py
```

## 최근 업데이트

- **API 기반 크롤러 추가**: YTN, MBC, JTBC 등 주요 언론사 API 크롤러 구현
- **MongoDB 통합**: 크롤링한 뉴스 데이터의 효율적인 저장 및 관리를 위한 MongoDB 연동
- **병렬 크롤링**: 비동기 I/O를 활용한 효율적인 병렬 크롤링 구현
- **URL 기반 중복 필터링**: 동일 기사의 중복 저장 방지 기능
- **모니터링 스크립트**: 데이터베이스 상태 확인을 위한 count_documents.py 스크립트 추가

## 개발자 가이드

### MongoDB 설정

`.env` 파일에 MongoDB 연결 정보를 설정하세요:

```env
MONGODB_URL=mongodb://root:1234@localhost:27017
MONGODB_DB_NAME=news_alert
```

### 새 크롤러 추가하기

새로운 뉴스 API 크롤러를 추가하려면:

1. `app/crawler/{source}/` 디렉토리 생성 (예: `app/crawler/kbs/`)
2. `BaseNewsCrawler`를 상속받는 크롤러 클래스 구현
3. `registry.py`에 새 크롤러 인스턴스 등록

### 주의사항

- MongoDB 객체 비교 시 `if db:` 대신 `if db is not None:` 사용
- API 호출 시 적절한 예외 처리와 로깅 포함
- 비동기 함수는 항상 `await` 키워드로 호출

## 향후 계획

- [ ] 크롤링 대상 언론사 추가
- [ ] 텍스트 분석 및 키워드 추출 기능 구현
- [ ] 사용자 맞춤형 알림 설정 기능
- [ ] 웹 인터페이스 구현

---

## 기여

이 프로젝트는 학습과 포트폴리오를 목적으로 하며, 누구든지 포크/개선/실험을 환영합니다!

---
