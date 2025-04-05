from app.crawler.base import BaseNewsCrawler
from app.crawler.mbc_hybrid import HybridMbcCrawler

CRAWLERS: dict[str, BaseNewsCrawler] = {
    "mbc": HybridMbcCrawler(),
    # 향후 "kbs": KbsNewsCrawler(), 등으로 쉽게 확장 가능
}
