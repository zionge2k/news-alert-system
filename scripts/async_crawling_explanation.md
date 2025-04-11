# 비동기 크롤링 코드 설명

## tasks 리스트 생성

```python
tasks = [run_crawler(name, crawler) for name, crawler in CRAWLERS.items()]
```

이 부분은 리스트 컴프리헨션을 사용하여 모든 크롤러에 대한 비동기 작업을 생성합니다.

예시:
```python
CRAWLERS = {
    "mbc": HybridMbcCrawler(),
    "ytn": YtnNewsApiCrawler(),
}
```

위와 같이 정의된 크롤러들이 있다면, tasks는 다음과 같이 생성됩니다:
```python
tasks = [
    run_crawler("mbc", HybridMbcCrawler()),
    run_crawler("ytn", YtnNewsApiCrawler())
]
```

## asyncio.gather() 동작 방식

```python
await asyncio.gather(*tasks)
```

`asyncio.gather()`는 여러 비동기 작업을 동시에 실행하고 모든 작업이 완료될 때까지 기다립니다.

### 작동 순서

1. MBC 크롤러 시작:
   ```python
   # MBC 크롤러가 네트워크 요청을 시작
   # 이때 CPU는 다른 작업을 할 수 있음
   ```

2. YTN 크롤러 시작:
   ```python
   # YTN 크롤러도 동시에 네트워크 요청을 시작
   # MBC와 YTN이 동시에 실행됨
   ```

3. 두 크롤러 모두 완료될 때까지 대기:
   ```python
   # MBC와 YTN 모두 완료될 때까지 기다림
   # 둘 중 하나가 먼저 완료되어도 다른 하나가 끝날 때까지 대기
   ```

### 실행 시간 예시

- MBC 크롤링: 10초
- YTN 크롤링: 8초
- 순차 실행 시: 18초 (10초 + 8초)
- `asyncio.gather()` 사용 시: 10초 (둘 중 더 오래 걸리는 시간)

### asyncio.gather()의 장점

1. 모든 크롤러가 동시에 실행됨
2. CPU 자원을 효율적으로 사용
3. 전체 실행 시간이 크게 단축됨
4. 한 크롤러가 실패해도 다른 크롤러는 계속 실행됨

이전 코드에서는 크롤러들이 순차적으로 실행되어 시간이 더 오래 걸렸지만, 이제는 모든 크롤러가 병렬로 실행되어 전체 실행 시간이 단축됩니다.

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
   - `TaskGroup`: 한 태스크에서 예외가 발생하면 모든 태스크가 취소됨 (Python 3.11의 새로운 기능)

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

3. **단순성**
   - 현재 사용 사례에서는 `gather()`의 기능으로 충분함
   - `TaskGroup`의 추가 기능(자동 취소 등)이 현재 요구사항에는 불필요함

4. **안정성**
   - `gather()`는 오랜 기간 사용되어 검증된 방식
   - `TaskGroup`은 상대적으로 새로운 기능으로, 아직 실전에서의 검증이 부족함 