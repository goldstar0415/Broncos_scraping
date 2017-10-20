import json
from datetime import datetime
from urllib.parse import urlencode

import pytz
from scrapy import Request

from hashtag import yesql
from hashtag.items import PostItem
from hashtag.spiders.spider import BaseSpider


class Instagram(BaseSpider):
    name = 'instagram'
    handle_httpstatus_list = [429]
    search_url = 'https://api.instagram.com/v1/tags/{tag}/media/recent?{params}'

    def _request_from_params(self, params):
        return Request(
            self.search_url.format(tag=self.tag_name[1:], params=urlencode(params)),
            meta=self._meta_proxy()
        )

    def start_requests(self):
        self.account = yesql.get_fresh_account(self.session, self.name)
        yield self._request_from_params({'access_token': self.account.token})

    def parse(self, response):
        if response.status == 429:
            self._set_next_account()
            newreq = response.request.copy()
            newreq.dont_filter=True
            newreq.headers=self._headers()
            return newreq

        jdata = json.loads(response.text)
        for post in jdata['data']:
            if self.last and post['id'] == self.last['lid']:
                return

            yield self.item_from_post(post)

        next_mid = jdata['pagination'].get('next_min_id')
        if next_mid:
            yield self._request_from_params({
                'access_token': self.account.token,
                'min_tag_id': next_mid
            })

    def item_from_post(self, post):
        cap = post['caption']
        item = PostItem(
            author_id=self.get_or_create_author(cap['from']) or '',
            elink='',
            link=post['link'],
            lid=post['id'],
            is_original=True,
            text=cap['text'],
            date_published=datetime.fromtimestamp(int(cap['created_time']), pytz.UTC),
            likes=post['likes']['count'],
            hashtags=['#{}'.format(x) for x in post['tags']]
        )

        images = sorted(post.get('images', {}).values(),
                        key=lambda x: x['width'],
                        reverse=True
        )
        if images:
            item['photo'] = images[0]['url']

        videos = sorted(post.get('videos', {}).values(),
                        key=lambda x: x['width'],
                        reverse=True
        )
        if videos:
            item['video'] = videos[0]['url']

        location = post.get('location')
        if location:
            item['geo'] = [location['latitude'], location['longitude']]

        return item

    def get_or_create_author(self, _from):
        lid = _from['id']
        author = self.db_author.find_one({"lid": lid})
        if not author:
            author = self.db_author.insert_one({
                'lid': lid,
                'link': 'http://instagram.com{}/'.format(_from['username']),
                'name': _from['full_name']
            })
            return str(author.inserted_id)

        return str(author['_id'])

    def _set_next_account(self):
        self.account.is_limited=True
        self.account.refresh_time=unow_tz() + timedelta(minutes=60)
        self.session.add(self.account)
        self.session.commit()
        self.account = yesql.get_fresh_account(self.session, self.name)
