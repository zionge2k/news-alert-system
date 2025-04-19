# 비동기 크롤링 시스템 설명

## 개요

이 문서는 뉴스 크롤링 시스템의 비동기 처리 방식과 전체 구조를 설명합니다. 모듈화된 접근 방식을 통해 크롤링과 저장 프로세스를 분리하여 코드의 가독성과 유지보수성을 향상시켰습니다.

## 시스템 구조

시스템은 다음과 같은 주요 컴포넌트로 구성되어 있습니다:

1. **scripts/crawl.py**: 크롤링 로직 전담 (실행 가능한 스크립트)
2. **scripts/save.py**: 데이터베이스 저장 로직 전담 (크롤링이 되어야 저장가능하기 때문에 단독사용 불가능)
3. **scripts/run_all.py**: 크롤링과 저장을 조합하여 실행하는 클라이언트 코드

## 실행 방법

Poetry를 사용하여 다음과 같이 스크립트를 실행할 수 있습니다:

### 전체 프로세스 실행 (크롤링 + DB 저장)

```bash
poetry run python scripts/run_all.py
```

### 크롤링만 실행

크롤링만 실행하고 DB에 저장하지 않으려면:
```bash
poetry run python scripts/run_all.py --no-save

# 또는 직접 크롤링 스크립트만 실행
poetry run python scripts/crawl.py
```

### 추가 옵션 사용

```bash
# 도움말 보기
poetry run python scripts/run_all.py --help
```

## 스크립트 목적

```text
뉴스 크롤링 및 MongoDB 저장 통합 스크립트

이 스크립트는 다양한 뉴스 소스에서 기사를 크롤링하고 MongoDB에 저장합니다.
병렬 크롤링으로 효율적으로 처리하며, 중복 기사는 자동으로 필터링합니다.

주요 기능:
1. 여러 뉴스 API 크롤러를 병렬로 실행하여 데이터를 수집
2. 수집된 기사의 URL을 기준으로 중복 확인
3. 신규 기사만 MongoDB에 저장
4. 수집 및 저장 과정에 대한 상세 로깅

사전 요구사항:
- MongoDB 연결 설정 (URL 및 인증 정보)
- 뉴스 크롤러 구현 (app/crawler/ 디렉토리)
- 모델 및 저장소 설정 (app/models/, db/repositories/)
```

## 크롤링 프로세스 (crawl.py)

`crawl.py`는 크롤링 작업만 담당하는 스크립트입니다. 핵심 기능:

### tasks 리스트 생성

```python
tasks = [run_crawler(name, crawler) for name, crawler in CRAWLERS.items()]
```

이 부분은 리스트 컴프리헨션을 사용하여 모든 크롤러에 대한 비동기 작업을 생성합니다.

### asyncio.gather() 동작 방식

```python
results = await asyncio.gather(*tasks, return_exceptions=True)
```

`asyncio.gather()`는 여러 비동기 작업을 동시에 실행하고 모든 작업이 완료될 때까지 기다립니다.

### 작동 순서

1. 크롤러 초기화 및 작업 생성
2. 모든 크롤러 병렬 실행 시작
3. 각 크롤러가 완료될 때까지 대기
4. 결과 수집 및 통합
5. 처리된 결과 반환

### 실행 시간 예시

병렬 처리의 장점은 실행 시간에서 명확하게 드러납니다:

- MBC 크롤링: 10초
- YTN 크롤링: 8초
- 순차 실행 시: 18초 (10초 + 8초)
- `asyncio.gather()` 사용 시: 10초 (둘 중 더 오래 걸리는 시간)

## 데이터베이스 저장 모듈 (save.py)

`save.py`는 MongoDB 저장 작업을 담당하는 라이브러리 모듈입니다:

```python
async def save_to_database(articles: List[ArticleDTO]) -> int:
```

이 함수는 크롤링된 기사를 MongoDB에 저장하며 다음과 같은 프로세스를 거칩니다:

1. 각 기사마다 플랫폼과 article_id 정보 추출
2. unique_id 또는 URL 기반 중복 검사
3. 신규 기사만 DB에 저장
4. 저장 결과 통계 기록 및 반환

### 중복 감지 로직

```python
# article_id 추출 시도
article_id: Optional[str] = getattr(article_dto.metadata, "article_id", None)

if article_id:
    # article_id가 있는 경우 복합키로 중복 확인
    unique_id: str = f"{platform}_{article_id}"
    existing = await article_repository.find_by_unique_id(unique_id)
else:
    # article_id가 없는 경우 URL로 검색
    existing = await article_repository.find_by_url(article_dto.url)
```

## 통합 실행 프로세스 (run_all.py)

`run_all.py`는 클라이언트 코드 역할을 하여 전체 프로세스를 조율합니다:

1. 명령줄 인자 파싱 (`--no-save` 등)
2. MongoDB 연결 초기화
3. 크롤링 수행 (`crawl.py`의 함수 호출)
4. `--no-save` 옵션이 없으면 DB 저장 (`save.py`의 함수 호출)
5. 연결 종료 및 결과 보고

## 모듈화의 장점

1. **관심사 분리**
   - 각 모듈이 한 가지 책임만 가짐 (단일 책임 원칙)
   - 코드 가독성 및 유지보수성 향상

2. **독립적 테스트 용이**
   - 각 컴포넌트를 독립적으로 테스트 가능
   - 특정 기능만 디버깅하기 쉬움

3. **유연한 실행 옵션**
   - 크롤링만 수행하는 등 유연한 실행이 가능
   - 명령줄 인자를 통한 동작 제어

## asyncio.gather() vs asyncio.TaskGroup

### TaskGroup 사용 예시

```python
async with asyncio.TaskGroup() as tg:
    for name, crawler in CRAWLERS.items():
        tg.create_task(run_crawler(name, crawler))
```

### 주요 차이점

1. **에러 처리 방식**
   - `gather()`: 한 태스크에서 예외가 발생해도 다른 태스크는 계속 실행됨
   - `TaskGroup`: 한 태스크에서 예외가 발생하면 모든 태스크가 취소됨 (Python 3.11의 기능)

2. **문법적 차이**
   - `gather()`: 리스트로 태스크를 모아서 한 번에 실행
   - `TaskGroup`: 컨텍스트 매니저를 사용하여 더 명시적인 리소스 관리

3. **호환성**
   - `gather()`: Python 3.7 이상에서 사용 가능
   - `TaskGroup`: Python 3.11 이상에서만 사용 가능

### gather()를 선택한 이유

1. **에러 격리**
   - 크롤러 중 하나가 실패해도 다른 크롤러는 계속 실행되어야 함
   - `gather()`는 이러한 요구사항에 더 적합함

2. **호환성**
   - `gather()`는 더 넓은 Python 버전에서 지원됨
   - 프로젝트의 Python 버전 요구사항을 더 유연하게 설정 가능