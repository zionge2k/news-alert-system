import logging

# 루트 로거의 기본 구성
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-5s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def get_logger(name: str) -> logging.Logger:
    """
    이름 기반 로거를 반환합니다. 일반적으로 모듈 이름을 넘겨줍니다.
    예: logger = get_logger(__name__)
    """
    return logging.getLogger(name)
