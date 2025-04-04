import asyncio
from app.crawler.registry import CRAWLERS

async def run_all(keyword: str = "탄핵"):
    print(f"\n['{keyword}' 키워드로 뉴스 수집 시작]\n")

    for name, crawler in CRAWLERS.items():
        print(f"== {name.upper()} ==")
        try:
            articles = await crawler.fetch_articles(keyword)
            if not articles:
                print("관련 뉴스 없음.")
            else:
                for article in articles:
                    print(f"• {article['title']}\n  → {article['link']}")
        except Exception as e:
            print(f" 크롤링 실패: {e}")
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(run_all())
