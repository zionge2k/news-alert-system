from app.crawler.base import BaseNewsCrawler
from app.crawler.jtbc.api import JTBCNewsApiCrawler
from app.crawler.mbc.api import MbcNewsApiCrawler
from app.crawler.ytn.api import YtnNewsApiCrawler

CRAWLERS: dict[str, BaseNewsCrawler] = {
    "mbc": MbcNewsApiCrawler(),
    "ytn": YtnNewsApiCrawler(),
    "jtbc": JTBCNewsApiCrawler(),
    # 향후 "kbs": KbsNewsCrawler(), 등으로 쉽게 확장 가능
}
