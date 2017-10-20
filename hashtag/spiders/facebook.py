import logging
import os
import re
import tempfile
import time
from datetime import datetime
from contextlib import contextmanager

import pytz
from PIL import Image
from python_anticaptcha import AnticaptchaClient
from scrapy import Request
from selenium import webdriver
from sqlalchemy.engine.url import make_url
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from hashtag.items import PostItem
from hashtag.shortcuts import captcha_to_text
from hashtag.spiders.spider import BaseSpider

# from hashtag.utils import ResponseMock

LOGGER.setLevel(logging.WARNING)


class Facebook(BaseSpider):
    name = 'facebook'
    search_url = 'https://www.facebook.com/hashtag/{}'
    hashex = re.compile('#[\w\-_\d]+')

    def start_requests(self):
        yield Request(
            self.search_url.format(self.tag_name[1:]),
            meta=self._meta_proxy()
        )

    def _get_phantom_proxy_args(self):
        # px = self.current_proxy.url
        # lpos = px.find('/') + 2
        # rpos = px.find('@')
        # creds = px[lpos:rpos]
        # _url = px[:lpos] + px[rpos+1:]
        # return [
        #     '--ignore-ssl-errors=true',
        #     '--proxy-type=https',
        #     '--ssl-protocol=any',
        #     '--proxy-auth={}'.format(creds),
        #     '--proxy={}'.format(_url),
        # ]
        # let's hope there are no `:` in the password string
        # http://user:
        url = make_url(self.current_proxy.url)
        return {
            'host': url.host,
            'port': url.port,
            'type': url.drivername,
            'username': url.username,
            'password': url.password
        }

    @contextmanager
    def _make_driver(self):
        dcaps = dict(DesiredCapabilities.PHANTOMJS)
        timest = str(time.time() * 10)[1:]
        dcaps["phantomjs.page.settings.userAgent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            "(KHTML, like Gecko) Chrome/{}.{}.{}.{} Safari/537.36"
        ).format(
            timest[:2],
            timest[2],
            timest[3:7],
            timest[7:9]
        )
        driver = webdriver.Remote(
            command_executor=self.settings.get("PHANTOMJS_URL"),
            desired_capabilities=dcaps,
            # is not supported on remote driver
            # service_args=self._get_phantom_proxy_args()
        )
        # should be phantomjs 2
        # for proxy setting to work
        driver.command_executor._commands['executePhantomScript'] = (
            'POST', '/session/$sessionId/phantom/execute')
        driver.execute(
            'executePhantomScript',
            {
                'script': (
                    'phantom.setProxy("{host}", {port}, '
                    '"{type}", "{username}", "{password}");'
                ).format(**self._get_phantom_proxy_args()),
                'args' : [] })
        try:
            yield driver
        finally:
            driver.close()

    def _ban_proxy_and_repeat(self, response):
        # self.current_proxy.is_banned = True
        self.proxies.remove(self.current_proxy)
        return Request(
            response.url,
            meta=self._meta_proxy(),
            dont_filter=True
        )

    def _save_captcha_image(self, driver):
        img = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((
                By.XPATH, "//img[contains(@src, 'captcha')]"
        )))
        captcha_fname = 'captcha_{}.png'.format(next(tempfile._get_candidate_names()))
        driver.save_screenshot(captcha_fname)
        cap = Image.open(captcha_fname)
        x, y = img.location['x'], img.location['y']
        cropped = cap.crop((
            x,
            y,
            x+img.size['width'],
            y+img.size['height']
        ))
        cropped.save(captcha_fname)
        return captcha_fname

    def _solve_captcha(self, cap_client, driver):
        cap_img = self._save_captcha_image(driver)
        cap_text = captcha_to_text(cap_client, cap_img)
        textbox = driver.find_element_by_id("captcha_response")
        textbox.send_keys(cap_text)
        textbox.send_keys(Keys.ENTER)
        os.remove(cap_img)

    def parse(self, response):
        with self._make_driver() as driver:
            driver.get(response.url)

            tries = 0
            cap_client = AnticaptchaClient(self.settings.get("ANTI_CAPTCHA_KEY"))
            while driver.find_elements_by_id("captcha_persist_data") and tries < 5:
                self._solve_captcha(cap_client, driver)
                WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((
                        By.ID, "BrowseResultsContainer"
                )))
                tries += 1
                # driver.save_screenshot("meh.png")
                # yield self._ban_proxy_and_repeat(response)
                # return

            skip = 0
            while skip<200:
                for post in driver.find_elements_by_xpath(
                        "//div[contains(@class, 'fbUserStory')]")[skip:]:
                    yield self.item_from_post(post)
                    skip += 1
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def item_from_post(self, post):
        text = post.find_element_by_xpath('.//div[contains(@class, "userContent")]').text
        link = self._get_post_link(post)

        item = PostItem(
            author_id=self.get_or_create_author(post),
            elink='',
            link=link,
            lid=link,
            is_original=True,
            text=text,
            date_published=self._get_pubdate(post),
            likes=self._get_likes(post),
            hashtags=self.hashex.findall(text)
        )

        maybe_img = post.find_elements_by_xpath(
                ".//div[contains(@class, 'uiScaledImageContainer')]/img")
        if maybe_img:
            item['photo'] = maybe_img[0].get_attribute("src")

        if post.find_elements_by_xpath(".//video"):
            # there's no other option
            item['video'] = item['link']

        maybe_elinks = post.find_elements_by_xpath((
            ".//div[contains(@class, 'userContent')]/"
            "following-sibling::node()//a[@tabindex='-1']"
        ))
        if maybe_elinks:
            item['elink'] = maybe_elinks[0].get_attribute('href')

        return item

    def get_or_create_author(self, post):
        link_el = post.find_element_by_xpath(".//h5//a")

        link = link_el.get_attribute('href').split('?')[0]
        # pic = link_el.find_element_by_xpath("./div/img").get_attribute("src")
        lid = link.split('/')[-2]
        author = self.db_author.find_one({"lid": lid})
        if not author:
            author = self.db_author.insert_one({
                'lid': lid,
                'link': link,
                'name': link_el.text,
                # 'pic': pic
            })
            return author.inserted_id

        return author['_id']

    def _get_pubdate(self, post):
        return datetime.fromtimestamp(
            int(
                post.find_element_by_xpath((
                    ".//a[contains(@class, 'fbPrivacyAudienceIndicator')]"
                    "//parent::node()//"
                    "abbr[boolean(@data-utime)]"
                )).get_attribute("data-utime")
            ),
            pytz.UTC)

    def _get_likes(self, post):
        maybe_likes = post.find_elements_by_xpath(
                ".//a[@data-comment-prelude-ref='action_link_bling']"
        )
        if maybe_likes:
            likestr = maybe_likes[0].get_attribute('aria-label').split(' ')[0]
            likes = re.sub('[.,\xa0]', '', likestr)
            if likes:
                return int(likes)
        return 0

    def _get_post_link(self, post):
        try:
            # well, that's fubar
            link = post.find_element_by_xpath((
                ".//a[contains(@class, 'fbPrivacyAudienceIndicator')]"
                "//parent::node()"
                "//abbr[boolean(@data-utime)]"
                "/ancestor::node()[2]"
                "//a"
            )).get_attribute("href")
            link = link.rsplit('?', 1)[0]
            return link
            # if link[-1] == '/':
            #     link = link[:-1]
        except:
            pass
