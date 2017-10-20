import json
from datetime import datetime
from urllib.parse import urlencode

from hashtag.items import PostItem
from hashtag import yesql
from hashtag.spiders.spider import BaseSpider
from scrapy import Request


class Pinterest(BaseSpider):
    name = 'pinterest'
    search_url = 'https://api.pinterest.com/v3/search/pins/'

    def start_requests(self):
        self.account = yesql.get_fresh_account(self.session, self.name)

        params = {
            'page_size': 250, # maximum
            'join': 'via_pinner,board,pinner',
            'query': self.tag_name,
            'access_token': self.account.token
        }
        yield Request(
            '{}?{}'.format(self.search_url, urlencode(params)),
            meta=self._meta_proxy()
        )

    def parse(self, response):
        search_result = json.loads(response.body)

        for pin in search_result['data']:
            if self.last and pin['id'] == self.last['lid']:
                return
            yield self._item_from_pin(pin)

    def _item_from_pin(self, pin):
        item = PostItem(
            author_id=None,
            elink=pin.get('link'),
            link='https://pinterest.com/pin/{}/'.format(pin['id']),
            lid=pin['id'],
            # country=noneget_in(original_tweet, ('place', 'country')),
            is_original=pin['is_repin'],
            text=pin['description'],
            date_published=datetime.strptime(
                pin['created_at'],
                '%a, %d %b %Y %H:%M:%S %z'),
            photo=pin.get('image_large_url', pin.get('image_medium_url')),
            shares=pin['repin_count']
        )

        if pin['is_video'] and 'attribution' in pin:
            key = 'embed_url' if pin['is_playable'] else 'url'
            item['video'] = pin['attribution'][key]

        return item
