#!/usr/bin/env python
"""
MongoDB 직접 테스트 스크립트 - 올바른 AsyncMock 처리 방식
"""
import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# 현재 경로를 Python path에 추가
current_dir = os.getcwd()
print(f"Current directory: {current_dir}")
sys.path.insert(0, current_dir)

# infra 모듈 가져오기
print("Importing infra module directly...")
from infra.database.mongodb import MongoDB

print("Successfully imported MongoDB class")


async def test_find():
    """find 메서드 테스트"""
    print("\n3. find 메서드 테스트")

    with patch("motor.motor_asyncio.AsyncIOMotorClient") as mock_client:
        # Mock 설정
        client_instance = MagicMock()
        mock_client.return_value = client_instance

        # admin mock
        admin_mock = MagicMock()
        client_instance.admin = admin_mock
        command_mock = AsyncMock()
        admin_mock.command = command_mock

        # 컬렉션 mock
        collection_mock = MagicMock()
        db_mock = MagicMock()
        client_instance.__getitem__.return_value = db_mock
        db_mock.__getitem__.return_value = collection_mock

        # 커서 mock
        cursor_mock = MagicMock()
        collection_mock.find.return_value = cursor_mock
        cursor_mock.sort.return_value = cursor_mock
        cursor_mock.skip.return_value = cursor_mock
        cursor_mock.limit.return_value = cursor_mock

        # to_list 메서드가 코루틴을 반환하도록 설정
        to_list_mock = AsyncMock()
        cursor_mock.to_list = to_list_mock
        to_list_mock.return_value = [{"_id": "1", "name": "test"}]

        # MongoDB 인스턴스 생성 및 연결
        mongo = MongoDB(uri="mongodb://localhost:27017", database="test_db")
        await mongo.connect()

        # find 메서드 테스트
        query = {"name": "test"}
        projection = {"_id": 1, "name": 1}
        sort = [("name", 1)]
        result = await mongo.find(
            "test_collection", query, projection, sort, limit=10, skip=5
        )

        # 검증
        print(f"  - collection.find 호출됨: {collection_mock.find.called}")
        print(
            f"  - find 인자: {collection_mock.find.call_args.args if collection_mock.find.called else 'N/A'}"
        )
        print(
            f"  - find 키워드 인자: {collection_mock.find.call_args.kwargs if collection_mock.find.called else 'N/A'}"
        )
        print(f"  - 커서.sort 호출됨: {cursor_mock.sort.called}")
        print(f"  - 커서.skip 호출됨: {cursor_mock.skip.called}")
        print(f"  - 커서.limit 호출됨: {cursor_mock.limit.called}")
        print(f"  - to_list 호출됨: {to_list_mock.called}")
        print(f"  - 결과: {result}")


async def manual_test():
    """MongoDB 구현을 수동으로 테스트"""
    print("\n== MongoDB 구현 테스트 ==")

    # 1. 정상적인 연결 테스트
    print("\n1. 정상적인 연결 테스트")

    with patch("motor.motor_asyncio.AsyncIOMotorClient") as mock_client:
        # Mock 설정
        client_instance = MagicMock()
        mock_client.return_value = client_instance

        admin_mock = MagicMock()
        client_instance.admin = admin_mock

        # admin.command가 코루틴을 반환하도록 설정
        command_mock = AsyncMock()
        admin_mock.command = command_mock

        # db 인스턴스 설정
        db_mock = MagicMock()
        client_instance.__getitem__.return_value = db_mock

        # MongoDB 인스턴스 생성 및 연결
        mongo = MongoDB(uri="mongodb://localhost:27017", database="test_db")
        db = await mongo.connect()

        # 검증
        print(f"  - AsyncIOMotorClient 호출됨: {mock_client.called}")
        print(f"  - admin.command('ping') 호출됨: {command_mock.called}")
        print(
            f"  - command 인자: {command_mock.call_args.args if command_mock.called else 'N/A'}"
        )
        print(f"  - 반환된 DB: {db is db_mock}")

        # 연결 해제 테스트
        print("\n2. 연결 해제 테스트")

        await mongo.disconnect()

        print(f"  - close 메서드 호출됨: {client_instance.close.called}")
        print(f"  - _client가 None으로 설정됨: {mongo._client is None}")
        print(f"  - _db가 None으로 설정됨: {mongo._db is None}")

    # 추가 테스트 실행
    await test_find()

    print("\n모든 테스트 완료")


if __name__ == "__main__":
    print("Running manual MongoDB tests...")
    asyncio.run(manual_test())
