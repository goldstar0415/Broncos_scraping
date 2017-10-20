# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from datetime import timedelta

import sqlalchemy as sa
from pymongo import DESCENDING, MongoClient
from scrapy.exceptions import DropItem

from hashtag.db import Session
from hashtag.models import HashTagNetwork, HashTag, Network, Proxy
from hashtag.shortcuts import unow_tz


class HashtagPipeline(object):
    def __init__(self, mongo_url, post_coll, author_coll):
        # session frees its resources on .commit()
        # so, there's no need to close it after committing
        self.session = Session()

        self._mongo_url = mongo_url
        self._post_name = post_coll
        self._author_name = author_coll

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings.get('MONGO_URL'),
                   crawler.settings.get('POST_TABLENAME'),
                   crawler.settings.get('AUTHOR_TABLENAME'))

    def _get_proxies(self):
        return list(
            self.session.query(Proxy).
            filter(Proxy.is_active==True).
            filter(Proxy.is_banned==False).
            filter(sa.or_(
                Proxy.expires>unow_tz()+timedelta(minutes=5),
                Proxy.expires==None
        )))

    def _get_last_for(self, tag_net):
        last = (self.db_post.
                find({
                    "network": tag_net.network.name,
                    "hashtags": {"$elemMatch": {
                        "$regex": tag_net.hashtag.tag,
                        "$options": "i"}},
                    "date_added": {"$lte": tag_net.last_scraped}
                }).
                sort("date_published", DESCENDING).
                limit(1)
        )

        if last.count():
            return last[0]

    def _get_tag_net(self, spider):
        return (
            self.session.query(HashTagNetwork).
            join(Network).
            join(HashTag).
            filter(HashTag.tag==spider.tag_name).
            filter(Network.name==spider.name).
            first()
        )

    def _update_tag_net(self, tag_net):
        tag_net.last_scraped = unow_tz()
        self.session.add(tag_net)
        self.session.commit()

    def open_spider(self, spider):
        self.mongo = MongoClient(self._mongo_url)
        db = self.mongo.get_default_database()
        self.db_post = db[self._post_name]

        tag_net = self._get_tag_net(spider)
        spider.proxies = self._get_proxies()
        spider.last = self._get_last_for(tag_net)
        spider.session = Session()
        spider.db_author = db[self._author_name]

        self._update_tag_net(tag_net)

    def process_item(self, item, spider):
        if not item['lid']:
            raise DropItem("Bad `lid`")

        for field in ('video', 'photo', 'elink', 'link', 'geo',
                      'city', 'country', 'text', 'title'):
            item.setdefault(field, '')
        item.setdefault('likes', None)
        item.setdefault('shares', None)
        item.setdefault('network', spider.name)
        item.setdefault('date_added', unow_tz())

        res = self.db_post.update(
            {"lid": item["lid"]},
            {"$set": dict(item)},
            upsert=True
        )
        return item

    def close_spider(self, spider):
        # maybe i should save tag as self.tag? FIXME: think of this later
        tag_net = self._get_tag_net(spider)
        self._update_tag_net(tag_net)
        # as i have said before, `.close()` in not needed. And `.commit()` has just been
        # executed inside `_update_tag()``

        spider.session.close()
        self.mongo.close()
