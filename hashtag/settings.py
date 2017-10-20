# -*- coding: utf-8 -*-

# Scrapy settings for hashtag project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'hashtag'

SPIDER_MODULES = ['hashtag.spiders']
NEWSPIDER_MODULE = 'hashtag.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {
   # 'hashtag.middlewares.HashtagSpiderMiddleware': 543,
    'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
}

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    # 'hashtag.middlewares.MyCustomDownloaderMiddleware': 543,
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 1,
    'scrapy_splash.SplashCookiesMiddleware': 723,
    'scrapy_splash.SplashMiddleware': 725,
    # or response encoding will be as broken as your heart when trying to understand
    # why nothing works.
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
}

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   'hashtag.pipelines.HashtagPipeline': 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'


from os import getenv

PROXY_TABLENAME = getenv('PROXY_TABLENAME', 'proxy')
ACCOUNT_TABLENAME = getenv('ACCOUNT_TABLENAME', 'account')
NETWORK_TABLENAME = getenv('NETWORK_TABLENAME', 'network')
HASHTAG_TABLENAME = getenv('HASHTAG_TABLENAME', 'hashtag')
HASHTAG_NETWORK_TABLENAME = getenv('HASHTAG_NETWORK_TABLENAME', 'hashtag_network')
AUTHOR_TABLENAME = getenv('AUTHOR_TABLENAME', 'author')
POST_TABLENAME = getenv('POST_TABLENAME', 'post')
USER_TABLENAME = getenv('USER_TABLENAME', 'user')
POSTGRES_URL = getenv('POSTGRES_URL', 'postgresql://hashtag:blahblah@localhost:8765/hashtag')
MONGO_URL = getenv('MONGO_URL', 'mongodb://localhost:27017/hashtags')
SCRAPYD_NODES = getenv('SCRAPYD_NODES', 'http://localhost:6800').split(';')
SPLASH_URL = getenv('SPLASH_URL', 'http://localhost:8050/')
ANTI_CAPTCHA_KEY = getenv("ANTI_CAPTCHA_KEY")
RABBIT_URI = getenv("RABBIT_URI", "localhost")
RABBIT_Q = getenv("RABBIT_Q", "tasks")
PHANTOMJS_URL = getenv("PHANTOMJS_URL", 'http://127.0.0.1:4444/wd/hub')
