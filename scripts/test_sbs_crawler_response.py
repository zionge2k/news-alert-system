#!/usr/bin/env python
"""
SBS 뉴스 API 응답 확인 스크립트
"""

import asyncio
import sys
from pathlib import Path

import aiohttp

# 프로젝트 루트 경로를 Python 경로에 추가
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

from app.crawler.utils.headers import create_sbs_headers


async def check_sbs_api_response():
    """SBS 뉴스 API 응답을 확인합니다."""
    print("SBS 뉴스 API 응답 확인 시작...")

    # API URL
    api_url = "https://news.sbs.co.kr/news/newsflash.do"

    # 요청 파라미터
    params = {
        "type": "json",
        "newestDate": "",
        "newestHour": "",
        "lastDate": "",
        "lastHour": "",
        "count": "20",
        "category": "01",  # 정치 카테고리
    }

    # 헤더 생성
    headers = create_sbs_headers()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params, headers=headers) as response:
                print(f"상태 코드: {response.status}")
                print(f"응답 헤더: {response.headers}")

                # 응답 내용 출력
                text = await response.text()
                print("\n응답 내용 (처음 500자):")
                print(text[:500])

                # Content-Type 확인
                content_type = response.headers.get("Content-Type", "")
                print(f"\nContent-Type: {content_type}")

                # 다른 URL 시도
                print("\n다른 URL 시도...")
                other_url = "https://news.sbs.co.kr/news/SectionNewsJson.do"
                other_params = {
                    "plink": "newsSection",
                    "sectionId": "01",
                }

                async with session.get(
                    other_url, params=other_params, headers=headers
                ) as other_response:
                    print(f"상태 코드: {other_response.status}")
                    print(f"응답 헤더: {other_response.headers}")

                    # 응답 내용 출력
                    other_text = await other_response.text()
                    print("\n응답 내용 (처음 500자):")
                    print(other_text[:500])

    except Exception as e:
        print(f"오류 발생: {str(e)}")


if __name__ == "__main__":
    asyncio.run(check_sbs_api_response())
