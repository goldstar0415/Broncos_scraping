import json
from datetime import datetime, timedelta
from urllib.parse import urlencode

from scrapy import Request

from hashtag import yesql
from hashtag.exceptions import SpiderAuthError
from hashtag.items import PostItem
from hashtag.shortcuts import unow_tz
from hashtag.spiders.spider import BaseSpider
from hashtag.utils import noneget_in


class Twitter(BaseSpider):
    name = 'twitter'
    search_url = 'https://api.twitter.com/1.1/search/tweets.json'

    def _headers(self):
        if self.account:
            return {'Authorization': 'Bearer {}'.format(self.account.token)}
        else:
            raise SpiderAuthError('Account pool exceeded for {}'.format(self.name))

    def start_requests(self):
        self.account = yesql.get_fresh_account(self.session, self.name)
        # Request.body does not work, LOL
        params = {
            'q': self.tag_name,
            'include_entities': True,
            'count': 100
        }
        yield Request(
            '{}?{}'.format(self.search_url, urlencode(params)),
            headers=self._headers(),
            errback=self.errback,
            callback=self.parse,
            meta=self._meta_proxy()
        )

    def parse(self, response):
        search_result = json.loads(response.body)

        for tweet in search_result['statuses']:
            if self.last and tweet['id'] == int(self.last['lid']):
                return
            yield self._item_from_tweet(tweet)

        # check if there's next page
        next_page = search_result['search_metadata'].get('next_results')
        if next_page:
            yield response.follow(
                next_page,
                errback=response.request.errback,
                callback=self.parse,
                headers=response.request.headers,
                meta=self._meta_proxy()
            )

    def _item_from_tweet(self, original_tweet):
        # Retweets can be distinguished from typical Tweets
        # by the existence of a retweeted_status attribute.
        # This attribute contains a representation of the original Tweet
        # that was retweeted.
        # see https://dev.twitter.com/overview/api/tweets
        tweet = original_tweet.get('retweeted_status') or original_tweet

        item = PostItem(
            author_id=self.get_or_create_author(original_tweet),
            elink=noneget_in(tweet, ('entities', 'urls', 0, 'expanded_url'), ''),
            link='https://twitter.com/{u}/status/{_id}'.format(
                u=tweet['user']['screen_name'],
                _id=tweet['id']
            ),
            lid=tweet['id_str'],
            country=noneget_in(original_tweet, ('place', 'country')),
            is_original=original_tweet['retweeted'],
            text=tweet['text'],
            date_published=datetime.strptime(
                tweet['created_at'],
                '%a %b %d %H:%M:%S %z %Y')
        )

        # so far I have seen only 'Polygon' geometry, not a 'Point'.
        # Maybe, we should use those in DB
        # if tweet['place']:

        if noneget_in(original_tweet, ('place', 'place_type')) == 'city':
            item['city']=original_tweet['place']['name']

        for media in noneget_in(tweet, ('extended_entities', 'media'), []):
            if media['type'] == 'video':
                item['video'] = media['video_info']['variants'][0]['url']
            elif media['type'] == 'photo':
                item['photo'] = media['media_url']

        item['hashtags'] = ['#{}'.format(h['text'])
                            for h in noneget_in(tweet, ['entities', 'hashtags'])]

        return item

    def get_or_create_author(self, tweet):
        lid = tweet['user']['id_str']
        author = self.db_author.find_one({"lid": lid})
        if not author:
            author = self.db_author.insert_one({
                'lid': lid,
                'link': 'http://twitter.com/{}'.format(tweet['user']['screen_name']),
                'name': tweet['user']['name'],
                'pic': tweet['user']['profile_image_url'].replace("_normal.jpg", '.jpg')
            })
            return author.inserted_id

        return author['_id']

    def errback(self, failure):
        # import pdb; pdb.set_trace()
        response = failure.value.response
        # check for proxy failure

        # twitter API limit reached
        if response.status == 429:
            self._set_next_account()
            newreq = failure.request
            newreq.dont_filter=True
            newreq.headers=self._headers()
            return newreq

    def _set_next_account(self):
        self.account.is_limited=True
        self.account.refresh_time=unow_tz() + timedelta(minutes=15)
        self.session.add(self.account)
        self.session.commit()
        self.account = yesql.get_fresh_account(self.session, self.name)
