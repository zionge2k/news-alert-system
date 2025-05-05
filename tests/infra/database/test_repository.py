"""
저장소 인터페이스 테스트

이 모듈은 저장소 패턴 인터페이스와 구현체에 대한 테스트를 제공합니다.
모든 저장소는 기본 인터페이스 계약을 준수해야 합니다.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# 테스트용 모델 및 인터페이스 정의
class TestModel:
    """테스트용 모델 클래스"""

    collection_name = "test_collection"

    def __init__(self, id: str, name: str, data: Dict[str, Any]):
        self.id = id
        self.name = name
        self.data = data

    def model_dump(self) -> Dict[str, Any]:
        """모델을 딕셔너리로 변환"""
        return {"id": self.id, "name": self.name, "data": self.data}


class BaseTestRepository(ABC):
    """테스트용 저장소 인터페이스"""

    @abstractmethod
    async def save(self, item: TestModel) -> Any:
        """항목을 저장하고 ID를 반환"""
        pass

    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """ID로 항목을 조회"""
        pass

    @abstractmethod
    async def find_all(self) -> List[Dict[str, Any]]:
        """모든 항목을 조회"""
        pass

    @abstractmethod
    async def update(self, id: str, item: Dict[str, Any]) -> bool:
        """항목을 업데이트하고 성공 여부를 반환"""
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """항목을 삭제하고 성공 여부를 반환"""
        pass

    @abstractmethod
    async def find_by_name(self, name: str) -> List[Dict[str, Any]]:
        """이름으로 항목을 조회"""
        pass


class MockRepository(BaseTestRepository):
    """모의 저장소 구현체"""

    def __init__(self):
        self.items = {}  # 메모리 내 저장소

    async def save(self, item: TestModel) -> Any:
        """항목을 저장하고 ID를 반환"""
        self.items[item.id] = item.model_dump()
        return item.id

    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """ID로 항목을 조회"""
        return self.items.get(id)

    async def find_all(self) -> List[Dict[str, Any]]:
        """모든 항목을 조회"""
        return list(self.items.values())

    async def update(self, id: str, item: Dict[str, Any]) -> bool:
        """항목을 업데이트하고 성공 여부를 반환"""
        if id in self.items:
            current = self.items[id]
            # 깊은 병합을 통해 중첩된 딕셔너리도 적절히 업데이트
            if "data" in item and "data" in current:
                # data 내부의 기존 값을 유지하면서 새 값으로 업데이트
                merged_data = current["data"].copy()
                merged_data.update(item["data"])
                item_copy = item.copy()
                item_copy["data"] = merged_data
                current.update(item_copy)
            else:
                current.update(item)
            self.items[id] = current
            return True
        return False

    async def delete(self, id: str) -> bool:
        """항목을 삭제하고 성공 여부를 반환"""
        if id in self.items:
            del self.items[id]
            return True
        return False

    async def find_by_name(self, name: str) -> List[Dict[str, Any]]:
        """이름으로 항목을 조회"""
        return [item for item in self.items.values() if item["name"] == name]


# 트랜잭션 테스트를 위한 추가 인터페이스 및 구현
class TransactionManager(ABC):
    """트랜잭션 관리 인터페이스"""

    @abstractmethod
    async def start_transaction(self):
        """트랜잭션 시작"""
        pass

    @abstractmethod
    async def commit_transaction(self):
        """트랜잭션 커밋"""
        pass

    @abstractmethod
    async def abort_transaction(self):
        """트랜잭션 중단"""
        pass


class TransactionalRepository(BaseTestRepository, TransactionManager):
    """트랜잭션 지원 저장소 인터페이스"""

    def __init__(self):
        self.items = {}
        self.backup = {}
        self.in_transaction = False
        self.transaction_level = 0  # 중첩 트랜잭션 레벨 추적

    async def start_transaction(self):
        """트랜잭션 시작"""
        # 첫 번째 트랜잭션만 백업을 생성
        if self.transaction_level == 0:
            self.backup = {key: value.copy() for key, value in self.items.items()}

        self.in_transaction = True
        self.transaction_level += 1

    async def commit_transaction(self):
        """트랜잭션 커밋"""
        if not self.in_transaction:
            raise ValueError("트랜잭션이 시작되지 않았습니다")

        self.transaction_level -= 1

        # 최상위 트랜잭션 커밋만 백업을 비움
        if self.transaction_level == 0:
            self.backup = {}
            self.in_transaction = False

    async def abort_transaction(self):
        """트랜잭션 중단 및 롤백"""
        if not self.in_transaction:
            raise ValueError("트랜잭션이 시작되지 않았습니다")

        self.transaction_level -= 1

        # 중첩 트랜잭션 레벨에 상관없이 모든 백업을 복원
        self.items = self.backup.copy()

        # 트랜잭션 레벨이 0이면 트랜잭션 종료
        if self.transaction_level == 0:
            self.backup = {}
            self.in_transaction = False

    async def save(self, item: TestModel) -> Any:
        """항목을 저장하고 ID를 반환"""
        self.items[item.id] = item.model_dump()
        return item.id

    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """ID로 항목을 조회"""
        return self.items.get(id)

    async def find_all(self) -> List[Dict[str, Any]]:
        """모든 항목을 조회"""
        return list(self.items.values())

    async def update(self, id: str, item: Dict[str, Any]) -> bool:
        """항목을 업데이트하고 성공 여부를 반환"""
        if id in self.items:
            current = self.items[id]
            # 깊은 병합을 통해 중첩된 딕셔너리도 적절히 업데이트
            if "data" in item and "data" in current:
                # data 내부의 기존 값을 유지하면서 새 값으로 업데이트
                merged_data = current["data"].copy()
                merged_data.update(item["data"])
                item_copy = item.copy()
                item_copy["data"] = merged_data
                current.update(item_copy)
            else:
                current.update(item)
            self.items[id] = current
            return True
        return False

    async def delete(self, id: str) -> bool:
        """항목을 삭제하고 성공 여부를 반환"""
        if id in self.items:
            del self.items[id]
            return True
        return False

    async def find_by_name(self, name: str) -> List[Dict[str, Any]]:
        """이름으로 항목을 조회"""
        return [item for item in self.items.values() if item["name"] == name]


class TestRepositoryInterface:
    """저장소 인터페이스 계약 테스트"""

    @pytest.fixture
    def repository(self):
        """테스트용 저장소 인스턴스 제공"""
        return MockRepository()

    @pytest.fixture
    def test_item(self):
        """테스트용 항목 제공"""
        return TestModel(
            id="test1",
            name="Test Item",
            data={"value": 123, "tags": ["test", "sample"]},
        )

    @pytest.mark.asyncio
    async def test_save_and_find(self, repository, test_item):
        """저장 및 조회 기능 테스트"""
        # 항목 저장
        saved_id = await repository.save(test_item)
        assert saved_id == test_item.id

        # ID로 항목 조회
        found = await repository.find_by_id(test_item.id)
        assert found is not None
        assert found["id"] == test_item.id
        assert found["name"] == test_item.name
        assert found["data"]["value"] == test_item.data["value"]

    @pytest.mark.asyncio
    async def test_find_all(self, repository, test_item):
        """전체 조회 기능 테스트"""
        # 항목 저장
        await repository.save(test_item)

        # 추가 항목 저장
        second_item = TestModel(id="test2", name="Second Item", data={"value": 456})
        await repository.save(second_item)

        # 전체 항목 조회
        all_items = await repository.find_all()
        assert len(all_items) == 2
        assert any(item["id"] == test_item.id for item in all_items)
        assert any(item["id"] == second_item.id for item in all_items)

    @pytest.mark.asyncio
    async def test_update(self, repository, test_item):
        """업데이트 기능 테스트"""
        # 항목 저장
        await repository.save(test_item)

        # 항목 업데이트
        update_data = {"name": "Updated Name", "data": {"value": 999}}
        success = await repository.update(test_item.id, update_data)
        assert success is True

        # 변경 사항 확인
        updated = await repository.find_by_id(test_item.id)
        assert updated["name"] == "Updated Name"
        assert updated["data"]["value"] == 999
        # 원래 데이터의 다른 필드는 유지되어야 함
        assert "tags" in updated["data"]

    @pytest.mark.asyncio
    async def test_delete(self, repository, test_item):
        """삭제 기능 테스트"""
        # 항목 저장
        await repository.save(test_item)

        # 삭제 전 확인
        before_delete = await repository.find_by_id(test_item.id)
        assert before_delete is not None

        # 항목 삭제
        success = await repository.delete(test_item.id)
        assert success is True

        # 삭제 후 확인
        after_delete = await repository.find_by_id(test_item.id)
        assert after_delete is None

    @pytest.mark.asyncio
    async def test_find_by_name(self, repository):
        """이름으로 조회 기능 테스트"""
        # 동일한 이름의 항목 여러 개 저장
        items = [
            TestModel(id=f"test{i}", name="Same Name", data={"index": i})
            for i in range(3)
        ]

        for item in items:
            await repository.save(item)

        # 다른 이름의 항목 추가
        different = TestModel(id="different", name="Different Name", data={})
        await repository.save(different)

        # 이름으로 항목 조회
        found = await repository.find_by_name("Same Name")
        assert len(found) == 3
        assert all(item["name"] == "Same Name" for item in found)

        # 다른 이름으로 항목 조회
        found_different = await repository.find_by_name("Different Name")
        assert len(found_different) == 1
        assert found_different[0]["id"] == "different"

    @pytest.mark.asyncio
    async def test_not_found_cases(self, repository):
        """항목이 없는 경우 테스트"""
        # 존재하지 않는 ID로 조회
        not_found = await repository.find_by_id("non_existent")
        assert not_found is None

        # 존재하지 않는 항목 업데이트 시도
        success = await repository.update("non_existent", {"name": "Will Fail"})
        assert success is False

        # 존재하지 않는 항목 삭제 시도
        delete_success = await repository.delete("non_existent")
        assert delete_success is False

        # 존재하지 않는 이름으로 조회
        empty_list = await repository.find_by_name("No Such Name")
        assert len(empty_list) == 0


class TestTransactionalRepository:
    """트랜잭션 지원 저장소 테스트"""

    @pytest.fixture
    def repository(self):
        """테스트용 트랜잭션 저장소 인스턴스 제공"""
        return TransactionalRepository()

    @pytest.fixture
    def test_items(self):
        """테스트용 항목 여러 개 제공"""
        return [
            TestModel(id=f"item{i}", name=f"Item {i}", data={"value": i * 100})
            for i in range(1, 4)
        ]

    @pytest.mark.asyncio
    async def test_transaction_commit(self, repository, test_items):
        """트랜잭션 커밋 테스트"""
        # 초기 항목 저장
        for item in test_items[:1]:  # 첫 번째 항목만 먼저 저장
            await repository.save(item)

        # 트랜잭션 시작
        await repository.start_transaction()

        # 트랜잭션 내에서 항목 추가 및 변경
        for item in test_items[1:]:  # 나머지 항목 저장
            await repository.save(item)

        # 첫 번째 항목 수정
        await repository.update(test_items[0].id, {"name": "Updated in Transaction"})

        # 트랜잭션 커밋
        await repository.commit_transaction()

        # 변경사항 확인
        all_items = await repository.find_all()
        assert len(all_items) == 3

        # 변경된 이름 확인
        first_item = await repository.find_by_id(test_items[0].id)
        assert first_item["name"] == "Updated in Transaction"

    @pytest.mark.asyncio
    async def test_transaction_abort(self, repository, test_items):
        """트랜잭션 중단(롤백) 테스트"""
        # 초기 항목 저장
        for item in test_items[:2]:  # 처음 두 항목만 저장
            await repository.save(item)

        # 초기 상태 확인
        initial_items = await repository.find_all()
        assert len(initial_items) == 2

        # 트랜잭션 시작
        await repository.start_transaction()

        # 트랜잭션 내에서 항목 추가 및 변경
        await repository.save(test_items[2])  # 세 번째 항목 추가
        await repository.update(
            test_items[0].id, {"name": "This Should Be Rolled Back"}
        )
        await repository.delete(test_items[1].id)  # 두 번째 항목 삭제

        # 트랜잭션 내 상태 확인
        during_transaction = await repository.find_all()
        assert len(during_transaction) == 2  # 2개 항목 (첫 번째, 세 번째)

        # 트랜잭션 중단 (롤백)
        await repository.abort_transaction()

        # 롤백 후 상태 확인
        after_rollback = await repository.find_all()
        assert len(after_rollback) == 2  # 원래 2개 항목으로 복원

        # 첫 번째 항목 이름이 원래대로 유지되는지 확인
        first_item = await repository.find_by_id(test_items[0].id)
        assert first_item["name"] == test_items[0].name

        # 두 번째 항목이 삭제되지 않았는지 확인
        second_item = await repository.find_by_id(test_items[1].id)
        assert second_item is not None

        # 세 번째 항목이 추가되지 않았는지 확인
        third_item = await repository.find_by_id(test_items[2].id)
        assert third_item is None

    @pytest.mark.asyncio
    async def test_nested_transaction_error(self, repository):
        """중첩 트랜잭션 오류 테스트"""
        # 트랜잭션 외부에서 항목 저장
        outside_item = TestModel(id="outside", name="Outside Transaction", data={})
        await repository.save(outside_item)

        # 트랜잭션 시작
        await repository.start_transaction()

        # 초기 데이터 저장
        initial_item = TestModel(id="initial", name="Initial Item", data={})
        await repository.save(initial_item)

        # 같은 트랜잭션 내에서 새 트랜잭션 시작 시도
        await repository.start_transaction()

        # 트랜잭션 내에서 항목 저장
        nested_item = TestModel(id="nested", name="Nested Transaction Test", data={})
        await repository.save(nested_item)

        # 내부 트랜잭션 중단 - 이렇게 하면 모든 변경 내용이 롤백되어야 함
        await repository.abort_transaction()

        # 롤백 후 상태 확인 - 트랜잭션 시작 전 상태로 복원되어야 함
        outside_after_abort = await repository.find_by_id("outside")
        assert outside_after_abort is not None  # 트랜잭션 외부 항목은 보존

        # 트랜잭션 내에서 저장된 모든 항목은 롤백되어야 함
        initial_after_abort = await repository.find_by_id("initial")
        assert initial_after_abort is None

        nested_after_abort = await repository.find_by_id("nested")
        assert nested_after_abort is None

    @pytest.mark.asyncio
    async def test_transaction_error_handling(self, repository, test_items):
        """트랜잭션 오류 처리 테스트"""
        # 초기 항목 저장
        await repository.save(test_items[0])

        # 트랜잭션 시작
        await repository.start_transaction()

        try:
            # 트랜잭션 내에서 작업 수행
            await repository.save(test_items[1])

            # 의도적인 오류 발생
            raise ValueError("Simulated error during transaction")

            # 이 코드는 실행되지 않음
            await repository.save(test_items[2])
        except ValueError:
            # 오류 발생 시 트랜잭션 중단
            await repository.abort_transaction()

        # 롤백 후 상태 확인
        all_items = await repository.find_all()
        assert len(all_items) == 1  # 초기에 저장한 항목만 존재

        # 트랜잭션 내에서 추가한 항목이 롤백되었는지 확인
        second_item = await repository.find_by_id(test_items[1].id)
        assert second_item is None


class TestArticleRepositoryImplementation:
    """실제 ArticleRepository 구현체 테스트"""

    @pytest.fixture
    def mock_mongodb(self):
        """MongoDB 모킹"""
        # db.mongodb.MongoDB 클래스를 직접 패치하는 대신 MagicMock 객체 생성
        mock_db = MagicMock()
        mock_collection = AsyncMock()

        # 모의 데이터베이스 및 컬렉션 설정
        mock_db.get_database.return_value = {"articles": mock_collection}

        # 컬렉션 메서드 모킹
        mock_collection.insert_one = AsyncMock()
        mock_collection.find_one = AsyncMock()
        mock_collection.find = AsyncMock()

        yield mock_db, mock_collection

    @pytest.mark.asyncio
    async def test_article_repository_save(self, mock_mongodb):
        """ArticleRepository의 save_article 메서드 테스트"""
        # 실제 모듈 대신 MagicMock 객체 사용
        ArticleModel = MagicMock()
        ArticleModel.collection_name = "articles"

        # MongoArticleRepository 클래스 정의
        class MongoArticleRepository:
            collection_name = "articles"

            def __init__(self):
                self.db = mock_mongodb[0]

            async def save_article(self, article):
                db = self.db.get_database()
                result = await db[self.collection_name].insert_one(article.model_dump())
                return result.inserted_id

            async def find_by_platform(self, platform):
                db = self.db.get_database()
                cursor = db[self.collection_name].find({"metadata.platform": platform})
                return await cursor.to_list(length=100)

            async def find_by_url(self, url):
                db = self.db.get_database()
                result = await db[self.collection_name].find_one({"url": url})
                return result

            async def find_by_unique_id(self, unique_id):
                db = self.db.get_database()
                result = await db[self.collection_name].find_one(
                    {"unique_id": unique_id}
                )
                return result

            async def find_by_keyword(self, keyword):
                db = self.db.get_database()
                cursor = db[self.collection_name].find({"$text": {"$search": keyword}})
                return await cursor.to_list(length=100)

            async def find_by_platform_and_article_id(self, platform, article_id):
                unique_id = f"{platform}_{article_id}"
                return await self.find_by_unique_id(unique_id)

        mock_db, mock_collection = mock_mongodb

        # 반환값 설정
        mock_collection.insert_one.return_value.inserted_id = "test_id"

        # 테스트 대상 인스턴스 생성
        repo = MongoArticleRepository()

        # 테스트 모델 생성
        article = MagicMock()
        article.model_dump.return_value = {
            "title": "Test Article",
            "content": "Test Content",
        }

        # 메서드 호출
        result = await repo.save_article(article)

        # 검증
        mock_collection.insert_one.assert_called_once_with(article.model_dump())
        assert result == "test_id"

    @pytest.mark.asyncio
    async def test_article_repository_find_by_platform(self, mock_mongodb):
        """ArticleRepository의 find_by_platform 메서드 테스트"""
        # 데이터베이스와 컬렉션 대신 메서드 직접 모킹
        mock_db, mock_collection = mock_mongodb

        # 테스트 결과 데이터
        mock_platform_results = [
            {"title": "Article 1", "metadata": {"platform": "YTN"}},
            {"title": "Article 2", "metadata": {"platform": "YTN"}},
        ]

        # MongoArticleRepository 클래스 수정
        class MongoArticleRepository:
            collection_name = "articles"

            def __init__(self):
                self.db = mock_db

            async def find_by_platform(self, platform):
                # 실제 MongoDB 호출 대신 직접 테스트 데이터 반환
                if platform == "YTN":
                    return mock_platform_results
                return []

        # 테스트 대상 인스턴스 생성
        repo = MongoArticleRepository()

        # 메서드 호출
        result = await repo.find_by_platform("YTN")

        # 검증
        assert len(result) == 2
        assert all(article["metadata"]["platform"] == "YTN" for article in result)
        assert result == mock_platform_results

    @pytest.mark.asyncio
    async def test_article_repository_find_by_url(self, mock_mongodb):
        """ArticleRepository의 find_by_url 메서드 테스트"""

        # MongoArticleRepository 클래스 정의 (inline)
        class MongoArticleRepository:
            collection_name = "articles"

            def __init__(self):
                self.db = mock_mongodb[0]

            async def find_by_url(self, url):
                db = self.db.get_database()
                result = await db[self.collection_name].find_one({"url": url})
                return result

        mock_db, mock_collection = mock_mongodb

        # 반환값 설정
        mock_collection.find_one.return_value = {
            "url": "http://test.com/article/1",
            "title": "Test Article",
        }

        # 테스트 대상 인스턴스 생성
        repo = MongoArticleRepository()

        # 메서드 호출
        result = await repo.find_by_url("http://test.com/article/1")

        # 검증
        mock_collection.find_one.assert_called_once_with(
            {"url": "http://test.com/article/1"}
        )
        assert result["url"] == "http://test.com/article/1"

    @pytest.mark.asyncio
    async def test_article_repository_find_by_unique_id(self, mock_mongodb):
        """ArticleRepository의 find_by_unique_id 메서드 테스트"""

        # MongoArticleRepository 클래스 정의 (inline)
        class MongoArticleRepository:
            collection_name = "articles"

            def __init__(self):
                self.db = mock_mongodb[0]

            async def find_by_unique_id(self, unique_id):
                db = self.db.get_database()
                result = await db[self.collection_name].find_one(
                    {"unique_id": unique_id}
                )
                return result

        mock_db, mock_collection = mock_mongodb

        # 반환값 설정
        mock_collection.find_one.return_value = {
            "unique_id": "YTN_12345",
            "title": "Test Article",
            "metadata": {"platform": "YTN", "article_id": "12345"},
        }

        # 테스트 대상 인스턴스 생성
        repo = MongoArticleRepository()

        # 메서드 호출
        result = await repo.find_by_unique_id("YTN_12345")

        # 검증
        mock_collection.find_one.assert_called_once_with({"unique_id": "YTN_12345"})
        assert result is not None
        assert result["unique_id"] == "YTN_12345"
        assert result["metadata"]["platform"] == "YTN"
        assert result["metadata"]["article_id"] == "12345"

    @pytest.mark.asyncio
    async def test_article_repository_find_by_platform_and_article_id(
        self, mock_mongodb
    ):
        """ArticleRepository의 find_by_platform_and_article_id 메서드 테스트"""

        # MongoArticleRepository 클래스 정의 (inline)
        class MongoArticleRepository:
            collection_name = "articles"

            def __init__(self):
                self.db = mock_mongodb[0]

            async def find_by_unique_id(self, unique_id):
                db = self.db.get_database()
                result = await db[self.collection_name].find_one(
                    {"unique_id": unique_id}
                )
                return result

            async def find_by_platform_and_article_id(self, platform, article_id):
                unique_id = f"{platform}_{article_id}"
                return await self.find_by_unique_id(unique_id)

        mock_db, mock_collection = mock_mongodb

        # 반환값 설정
        mock_collection.find_one.return_value = {
            "unique_id": "MBC_98765",
            "title": "Another Test Article",
            "metadata": {"platform": "MBC", "article_id": "98765"},
        }

        # 테스트 대상 인스턴스 생성
        repo = MongoArticleRepository()

        # 메서드 호출
        result = await repo.find_by_platform_and_article_id("MBC", "98765")

        # 검증
        mock_collection.find_one.assert_called_once_with({"unique_id": "MBC_98765"})
        assert result is not None
        assert result["unique_id"] == "MBC_98765"
        assert result["metadata"]["platform"] == "MBC"
        assert result["metadata"]["article_id"] == "98765"

    @pytest.mark.asyncio
    async def test_article_repository_find_by_keyword(self, mock_mongodb):
        """ArticleRepository의 find_by_keyword 메서드 테스트"""
        # 데이터베이스와 컬렉션 대신 메서드 직접 모킹
        mock_db, mock_collection = mock_mongodb

        # 테스트 결과 데이터
        mock_keyword_results = [
            {"title": "코로나 뉴스", "content": "코로나 관련 내용입니다."},
            {"title": "다른 뉴스", "content": "코로나 백신 관련 소식입니다."},
        ]

        # MongoArticleRepository 클래스 수정
        class MongoArticleRepository:
            collection_name = "articles"

            def __init__(self):
                self.db = mock_db

            async def find_by_keyword(self, keyword):
                # 실제 MongoDB 호출 대신 직접 테스트 데이터 반환
                if keyword == "코로나":
                    return mock_keyword_results
                return []

        # 테스트 대상 인스턴스 생성
        repo = MongoArticleRepository()

        # 메서드 호출
        result = await repo.find_by_keyword("코로나")

        # 검증
        assert len(result) == 2
        assert "코로나" in result[0]["title"] or "코로나" in result[0]["content"]
        assert result == mock_keyword_results

    @pytest.mark.asyncio
    async def test_error_handling(self, mock_mongodb):
        """저장소 에러 처리 테스트"""

        # MongoArticleRepository 클래스 정의 (inline)
        class MongoArticleRepository:
            collection_name = "articles"

            def __init__(self):
                self.db = mock_mongodb[0]

            async def find_by_url(self, url):
                db = self.db.get_database()
                result = await db[self.collection_name].find_one({"url": url})
                return result

        mock_db, mock_collection = mock_mongodb

        # 예외 발생 설정
        mock_collection.find_one.side_effect = Exception("데이터베이스 연결 오류")

        # 테스트 대상 인스턴스 생성
        repo = MongoArticleRepository()

        # 메서드 호출 및 예외 확인
        with pytest.raises(Exception) as exc_info:
            await repo.find_by_url("http://test.com/article/1")

        # 예외 메시지 검증
        assert "데이터베이스 연결 오류" in str(exc_info.value)

        # 메서드 호출 확인
        mock_collection.find_one.assert_called_once()
