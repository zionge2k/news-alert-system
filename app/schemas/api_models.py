from typing import Any, ClassVar, Dict, Optional

from pydantic import BaseModel, Field, model_validator


class BaseApiModel(BaseModel):
    """API 응답을 위한 기본 Pydantic 모델"""

    model_config = {
        "populate_by_name": True,
        "extra": "ignore",
    }

    # 기본값 매핑을 위한 클래스 변수 (서브클래스에서 오버라이드)
    _default_values: ClassVar[Dict[str, Any]] = {}

    @model_validator(mode="before")
    @classmethod
    def set_defaults_for_none_values(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """None 값을 적절한 기본값으로 설정"""
        if not isinstance(data, dict):
            return data

        # 자식 클래스에서 정의한 기본값 사용
        defaults = cls._default_values

        # None 값을 기본값으로 대체
        for field, default in defaults.items():
            if field in data and data[field] is None:
                data[field] = default

        return data

    @classmethod
    def safe_validate(cls, data: Dict[str, Any]) -> Optional["BaseApiModel"]:
        """예외 처리가 포함된 안전한 검증 메서드"""
        try:
            return cls.model_validate(data)
        except Exception as e:
            # 로깅 추가 가능
            return None
