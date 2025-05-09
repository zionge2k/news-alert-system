from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

T = TypeVar("T")  # 도메인 모델 타입
ID = TypeVar("ID")  # ID 타입 (보통 str이나 int)


class Repository(Generic[T, ID], ABC):
    """
    모든 저장소 구현체의 기본 인터페이스입니다.
    """

    @abstractmethod
    async def save(self, entity: T) -> T:
        """
        엔티티를 저장하고 저장된 엔티티를 반환합니다.
        """
        pass

    @abstractmethod
    async def find_by_id(self, id: ID) -> Optional[T]:
        """
        ID로 엔티티를 조회합니다.
        """
        pass

    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """
        모든 엔티티를 조회합니다.
        """
        pass

    @abstractmethod
    async def update(self, id: ID, data: Dict[str, Any]) -> Optional[T]:
        """
        엔티티를 업데이트합니다.
        """
        pass

    @abstractmethod
    async def delete(self, id: ID) -> bool:
        """
        엔티티를 삭제합니다.
        """
        pass


class Service(ABC):
    """
    모든 서비스 구현체의 기본 인터페이스입니다.

    이 인터페이스는 도메인 서비스의 공통 계약을 정의합니다.
    서비스는 도메인 모델의 비즈니스 로직을 조정하고 저장소와 상호 작용합니다.
    """

    pass
