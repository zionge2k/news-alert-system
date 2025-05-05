#!/usr/bin/env python
"""
간단한 임포트 테스트
"""
import os
import sys

# 현재 경로 출력
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

# 프로젝트 루트 추가
sys.path.insert(0, os.getcwd())

try:
    # 임포트 시도
    from infra.database.mongodb import MongoDB

    print("성공: MongoDB 클래스를 가져왔습니다.")

    # MongoDB 인스턴스 생성
    mongo = MongoDB(uri="mongodb://localhost:27017", database="test")
    print(f"MongoDB 인스턴스: {mongo}")

except ImportError as e:
    print(f"실패: {e}")
