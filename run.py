import sys

import sqlalchemy as sa

from builder import build
from hashtag import settings
from hashtag.contexts import session_scope
from hashtag.db import Session
from hashtag.models import HashTag, Network, HashTagNetwork
from hashtag.shortcuts import unow_tz
from hashtag.utils import dog_sleep
from scheduler import ScrapyScheduler


def get_tags(session):
    return (
        session.query(HashTagNetwork).
        join(Network).
        filter(
            sa.or_(
                HashTagNetwork.last_scraped==None,
                sa.func.trunc(
                    sa.extract('epoch', unow_tz()) -
                    sa.extract('epoch', HashTagNetwork.last_scraped)
                ) > Network.parsing_frequency)))


def main(scheduler):
    with session_scope(Session) as session:
        tags = get_tags(session)
        scheduler.schedule_many(list(tags))


def make_scheduler():
    return ScrapyScheduler(
        'hashtag',
        settings.SCRAPYD_NODES
    )

if __name__ == '__main__':
    scheduler = make_scheduler()
    egg = build()
    scheduler.load_egg(egg)
    try:
        while 1:
            main(scheduler)
            dog_sleep(10)
    except KeyboardInterrupt:
        sys.exit()
