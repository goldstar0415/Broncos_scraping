# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class PostItem(scrapy.Item):
    video = scrapy.Field()
    photo = scrapy.Field()
    elink = scrapy.Field()
    link = scrapy.Field()
    lid = scrapy.Field()
    geo = scrapy.Field()
    city = scrapy.Field()
    country = scrapy.Field()
    is_original = scrapy.Field()
    text = scrapy.Field()
    heading = scrapy.Field()
    date_published = scrapy.Field()
    date_added = scrapy.Field()
    hashtags = scrapy.Field()
    author_id = scrapy.Field()
    network = scrapy.Field()
    title = scrapy.Field()
    likes = scrapy.Field()
    shares = scrapy.Field()
