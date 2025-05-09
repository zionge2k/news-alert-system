#!/usr/bin/env python
"""
SBS 뉴스 웹사이트 HTML 구조 확인 스크립트
"""

import asyncio
import sys
from pathlib import Path

import aiohttp
from bs4 import BeautifulSoup

# 프로젝트 루트 경로를 Python 경로에 추가
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

from app.crawler.utils.headers import create_sbs_headers


async def check_sbs_html():
    """SBS 뉴스 웹사이트 HTML 구조를 확인합니다."""
    print("SBS 뉴스 웹사이트 HTML 구조 확인 시작...")

    # 정치 카테고리 URL
    url = "https://news.sbs.co.kr/news/newsMain.do?div=politics"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=create_sbs_headers()) as response:
                if response.status != 200:
                    print(f"요청 실패 - 상태 코드: {response.status}")
                    return

                html = await response.text()

                # BeautifulSoup으로 HTML 파싱
                soup = BeautifulSoup(html, "html.parser")

                # 뉴스 목록 영역 찾기 시도
                print("\n=== 주요 뉴스 섹션 찾기 ===")
                main_news = soup.select("div.w_news_list")
                print(f"w_news_list 클래스를 가진 div 요소 수: {len(main_news)}")

                # 다른 뉴스 목록 클래스 찾기
                print("\n=== 다른 뉴스 목록 클래스 찾기 ===")
                news_lists = soup.select("[class*=news_list]")
                print(
                    f"'news_list'를 포함하는 클래스를 가진 요소 수: {len(news_lists)}"
                )
                for i, elem in enumerate(news_lists[:3], 1):
                    print(f"\n[요소 {i}]")
                    print(f"태그: {elem.name}")
                    print(f"클래스: {elem.get('class')}")
                    print(f"자식 요소 수: {len(list(elem.children))}")

                # 실제 뉴스 기사 링크 찾기
                print("\n=== 뉴스 기사 링크 찾기 ===")
                news_links = soup.select("a[href*=news_id]")
                print(
                    f"'news_id'를 포함하는 href 속성을 가진 a 요소 수: {len(news_links)}"
                )
                for i, link in enumerate(news_links[:5], 1):
                    print(f"\n[링크 {i}]")
                    print(f"href: {link.get('href')}")
                    print(f"텍스트: {link.text.strip()[:50]}...")

                # 뉴스 헤드라인 섹션 찾기
                print("\n=== 뉴스 헤드라인 섹션 찾기 ===")
                headlines = soup.select("div.headline_list")
                print(f"headline_list 클래스를 가진 div 요소 수: {len(headlines)}")
                if headlines:
                    headline_items = headlines[0].select("li")
                    print(f"헤드라인 목록 내 li 요소 수: {len(headline_items)}")
                    for i, item in enumerate(headline_items[:3], 1):
                        print(f"\n[헤드라인 {i}]")
                        link = item.select_one("a")
                        if link:
                            print(f"href: {link.get('href')}")
                            print(f"텍스트: {link.text.strip()[:50]}...")

                # 페이지 전체 구조 요약
                print("\n=== 페이지 구조 요약 ===")
                body = soup.select_one("body")
                if body:
                    main_divs = body.select("> div")
                    print(f"body 직계 div 요소 수: {len(main_divs)}")
                    for i, div in enumerate(main_divs, 1):
                        div_id = div.get("id", "없음")
                        div_class = div.get("class", ["없음"])
                        print(f"div #{i} - ID: {div_id}, 클래스: {div_class}")

    except Exception as e:
        print(f"오류 발생: {str(e)}")


if __name__ == "__main__":
    asyncio.run(check_sbs_html())
