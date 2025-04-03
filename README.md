# 🔍 실시간 뉴스 수집/분석/알림 시스템

## 소개

이 프로젝트는 여러 언론사의 뉴스 웹사이트를 비동기 방식으로 크롤링하고, 텍스트 전처리 및 키워드 분석을 거쳐 특정 키워드(예: 주식, 경제, 사건 등)를 포함한 뉴스에 대해 Slack 알림을 전송하는 시스템입니다.

> ⚙️ 이 프로젝트는 **Python 3.11 이상**, **Poetry**를 사용하여 의존성을 관리하며, **Docker Compose**를 기반으로 누구나 동일한 환경에서 실행할 수 있도록 설계되었습니다.

## 주요 기능

- ✅ **비동기 크롤링**: `aiohttp` + `BeautifulSoup4`
- ✅ **작업 큐 처리**: `Redis` 또는 `RabbitMQ`
- ✅ **분석 및 전처리**: 키워드 기반 텍스트 분석
- ✅ **알림 전송**: Slack Webhook 연동
- ✅ **결과 API 제공**: `FastAPI`
- ✅ **뉴스 저장**: `PostgreSQL`

## 프로젝트 구조

```
news-alert-system/
├── app/                    # 핵심 애플리케이션 코드
│   ├── crawler/            # 비동기 뉴스 크롤러
│   ├── processor/          # 텍스트 전처리 및 키워드 분석
│   ├── notifier/           # Slack 알림 모듈
│   ├── api/                # FastAPI 엔드포인트
│   └── models/             # DB 모델 정의
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

- 이 명령어 하나로 Redis/PostgreSQL 등 필요한 모든 서비스가 함께 실행됩니다.
- 이후 `http://localhost:8000/docs`에서 API 문서를 확인할 수 있습니다.

### 2. 개발 환경 설정 (Poetry)

```bash
poetry install
poetry shell
```

> `.env` 파일 등 필요한 환경변수는 추후 `env.example`로 제공 예정입니다.

## 향후 계획

- [ ] 크롤링 대상 언론사 추가

---

## 기여

이 프로젝트는 학습과 포트폴리오를 목적으로 하며, 누구든지 포크/개선/실험을 환영합니다!

---
