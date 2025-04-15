from app.crawler.base import BaseNewsCrawler
from app.crawler.jtbc.api import JTBCNewsApiCrawler
from app.crawler.mbc.hybrid import HybridMbcCrawler
from app.crawler.ytn.api import YtnNewsApiCrawler

CRAWLERS: dict[str, BaseNewsCrawler] = {
    "mbc": HybridMbcCrawler(),
    "ytn": YtnNewsApiCrawler(),
    "jtbc": JTBCNewsApiCrawler(),
    # 향후 "kbs": KbsNewsCrawler(), 등으로 쉽게 확장 가능
}
