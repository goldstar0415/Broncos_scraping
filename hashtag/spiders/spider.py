import random

from scrapy import Spider
from hashtag.exceptions import SpiderProxyError


class BaseSpider(Spider):
    def __init__(self, *args, **kwargs):
        self.tag_name = kwargs['tag_name']
        self.current_proxy = None
        super().__init__(*args, **kwargs)

    def _meta_proxy(self):
        if self.proxies:
            self.current_proxy = random.choice(self.proxies)
            return {'proxy': self.current_proxy.url}
        else:
            raise SpiderProxyError("Proxy pool exceeded; shutting down.")
