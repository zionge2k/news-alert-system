from app.crawler.base import BaseNewsCrawler
from app.crawler.mbc import MbcPoliticsCrawler

CRAWLERS: dict[str, BaseNewsCrawler] = {
    "mbc": MbcPoliticsCrawler(),
    # 향후 "kbs": KbsNewsCrawler(), 등으로 쉽게 확장 가능
}
