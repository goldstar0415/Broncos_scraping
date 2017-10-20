import json
import re
from datetime import datetime
from urllib.parse import urlencode

from scrapy import FormRequest, Request
from scrapy_splash import SplashRequest

from hashtag import yesql
from hashtag.items import PostItem
from hashtag.spiders.spider import BaseSpider
from hashtag.utils import get_first


class Linkedin(BaseSpider):
    name = 'linkedin'
    login_url = 'https://www.linkedin.com/uas/login'
    search_url = 'https://www.linkedin.com/search/results/content/'

    def check_logged_in(self, response):
        cookies = response.headers.getlist('Set-Cookie')
        cookies = b';'.join(cookies)

        params = {
            'keywords': self.tag_name,
            'origin': 'HASH_TAG_FROM_POSTS',
            'facetSortBy':'date_posted'
        }
        return SplashRequest(
            '{}?{}'.format(self.search_url, urlencode(params)),
            self.parse,
            headers={'Cookie': cookies},
            endpoint='render.json',
            args={
                'wait': 5,
                **self._meta_proxy(),
                'html': 1,
            },
            meta={
                'download_timeout': 30,
                'dont_retry': True,
        })

    def login_callback(self, response):
        return FormRequest.from_response(
            response,
            formdata={
                'session_key': self.account.login,
                'session_password': self.account.password
            },
            callback=self.check_logged_in,
            meta=self._meta_proxy()
        )

    def start_requests(self):
        self.account = yesql.get_fresh_account(self.session, self.name)
        yield Request(
            self.login_url,
            self.login_callback,
            meta=self._meta_proxy()
        )

    def parse(self, response):
        posts = response.xpath('//li[re:test(@class, "search-content__result")]')
        json_data = self._steal_json(response)
        for post in posts:
            post_text = ''.join(post.xpath('.//p/.//span/text()').extract())
            maybe_elink = post.xpath('.//a[@target="_blank"]/@href').extract()

            lid = post.xpath('.//article/@data-id')[0].extract()

            yield PostItem(
                author_id=self.get_or_create_author(post) or '',
                elink=maybe_elink[0] if maybe_elink else '',
                link='http://linkedin.com/feed/update/{}/'.format(lid),
                lid=lid,
                country='',
                is_original=True,
                text=post_text,
                date_published=self._get_pubtime(lid, json_data),
                photo=self._get_image(lid, json_data),
                hashtags=re.findall('#[\w\d]+', post_text)
            )

    def _steal_json(self, response):
        code_tag = response.xpath(
            '//code[re:test(text(), "HASH_TAG_FROM_POSTS")]/text()'
        )[0].extract()
        return json.loads(code_tag)

    def get_or_create_author(self, post):
        uri = post.xpath('.//a[@data-control-name="actor"]/@href')[0].extract()
        lid = uri.split('/')[-2] # because it ends with '/'

        author = self.db_author.find_one({"lid": lid})
        if not author:
            author_name = post.xpath(
                '//span[re:test(@class,"feed-s-post-meta__name")]/span/text()'
            )[0].extract()
            pic = post.xpath(
                ".//img[contains(@class, 'presence-entity__image')]/@src"
            )[0].extract()

            author = self.db_author.insert_one({
                'lid': lid,
                'link': 'http://linkedin.com{}'.format(uri),
                'name': author_name,
                'pic': pic if pic.startswith('http') else None
            })
            return author.inserted_id

        return author['_id']


    def _get_image(self, lid, alljson):
        selector = lambda j: (
            j['$type'] == 'com.linkedin.voyager.common.MediaProxyImage' and
            lid in j.get('$id', '')
        )
        item = get_first(alljson['included'], selector)
        return item['url'] if item else ''

    def _get_pubtime(self, lid, alljson):
        selector = lambda j: (
            j['$type'] in ('com.linkedin.voyager.feed.ShareUpdate',
                           'com.linkedin.voyager.feed.Reshare') and
            j.get('urn') == lid
        )
        item = get_first(alljson['included'], selector)
        return datetime.fromtimestamp(item['createdTime']/1000)
