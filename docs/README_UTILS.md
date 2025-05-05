# Utils 패키지 문서

## 개요

`utils` 패키지는 애플리케이션 전반에서 사용되는 공통 유틸리티 기능을 제공합니다. 이 패키지는 기존의 `common/utils` 패키지를 대체하는 새로운 구조입니다.

## 패키지 구조

```
utils/
├── __init__.py          # 패키지 진입점 및 모든 공개 API 정의
├── config.py            # 설정 관리 유틸리티
├── exceptions.py        # 예외 처리 유틸리티
├── logger.py            # 로깅 유틸리티
├── http.py              # HTTP 요청 관련 유틸리티
├── json_utils.py        # JSON 데이터 처리 유틸리티
├── datetime_utils.py    # 날짜 및 시간 처리 유틸리티
└── text_utils.py        # 텍스트 처리 유틸리티
```

## 모듈 설명

### config.py

설정 관리를 위한 유틸리티를 제공합니다.

```python
from utils.config import Config, ConfigEnvironment, global_config

# 설정 객체 생성
config = Config()

# 파일에서 설정 로드
config = Config.load_from_file('config.yaml')

# 설정값 조회 및 설정
value = config.get('key', 'default_value')
config.set('key', 'new_value')

# 환경별 설정 확인
env = config.environment  # ConfigEnvironment 열거형
```

### exceptions.py

애플리케이션 전체에서 일관된 예외 처리를 위한 유틸리티를 제공합니다.

```python
from utils.exceptions import ValidationException, wrap_exception, exception_handler

# 예외 발생
raise ValidationException("유효하지 않은 데이터", code="INVALID_DATA")

# 외부 예외 래핑
try:
    # 외부 라이브러리 코드
    pass
except Exception as e:
    raise wrap_exception(e, ValidationException, "유효성 검사 실패")

# 데코레이터를 사용한 일관된 예외 처리
@exception_handler
def my_function():
    # 함수 코드
    pass
```

### logger.py

로깅을 위한 유틸리티를 제공합니다.

```python
from utils.logger import get_logger, setup_file_logging

# 모듈별 로거 생성
logger = get_logger(__name__)

# 로깅
logger.debug("디버그 메시지")
logger.info("정보 메시지")
logger.warning("경고 메시지")
logger.error("오류 메시지")

# 파일 로깅 설정
setup_file_logging('logs/app.log', log_level='info')
```

### http.py

HTTP 요청 관련 유틸리티를 제공합니다.

```python
from utils.http import create_request_headers

# 표준 HTTP 헤더 생성
headers = create_request_headers(
    user_agent="My App/1.0",
    referer="https://example.com",
    accept_language="ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
)
```

### json_utils.py

JSON 데이터 처리를 위한 유틸리티를 제공합니다.

```python
from utils.json_utils import clean_json_keys

# JSON 키 정리
data = {
    "First Name": "John",
    "Last-Name": "Doe",
    "user-Profile": {
        "User-Age": 30
    }
}
cleaned_data = clean_json_keys(data)
# 결과: {"first_name": "John", "last_name": "Doe", "user_profile": {"user_age": 30}}
```

### datetime_utils.py

날짜 및 시간 처리를 위한 유틸리티를 제공합니다.

```python
from utils.datetime_utils import get_current_timestamp, format_datetime

# 현재 시간 타임스탬프 조회
timestamp = get_current_timestamp()

# 날짜 포맷팅
formatted_date = format_datetime("2025-05-05T12:30:45", 
                               output_format="%Y년 %m월 %d일 %H시 %M분", 
                               timezone="Asia/Seoul")
```

### text_utils.py

텍스트 처리를 위한 유틸리티를 제공합니다.

```python
from utils.text_utils import sanitize_text, remove_html_tags

# 텍스트 정리
clean_text = sanitize_text("Hello <script>alert('XSS')</script>", max_length=50)

# HTML 태그 제거
plain_text = remove_html_tags("<p>Hello <b>World</b></p>")
# 결과: "Hello World"
```

## 마이그레이션 가이드

### 이전 임포트 방식 (deprecated)

```python
from common.utils import Config, get_logger
```

### 새로운 임포트 방식 (권장)

**패키지 수준 임포트:**

```python
from utils import Config, get_logger
```

**또는 직접 모듈 임포트:**

```python
from utils.config import Config
from utils.logger import get_logger
```

레거시 임포트는 계속 작동하지만 더 이상 사용되지 않음(deprecated) 경고가 표시됩니다. 새로운 코드는 위의 권장 임포트 방식을 사용해야 합니다. 