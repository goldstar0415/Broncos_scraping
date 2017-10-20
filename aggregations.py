from pymongo import DESCENDING, MongoClient
from functools import partial

from hashtag import settings
from hashtag.shortcuts import unow_tz


def latest_n_older_than(collection, n, _since):
    """
    returns latest n objects published earlier than _dt
    """
    return list(
        collection.find({
            "$query": {"date_published": {"$lte": _since}},
            "$orderby": {"date_published": DESCENDING}}
        ).limit(n))


def hourly_mentions_within_range(collection, hashtag, _since, _until, group_filter=None):
    """
    Returns number of mentions by hours for hashtag
    """
    group_filter = group_filter or {}
    cur = collection.aggregate([
        {"$match": {
            "date_published": {
                "$gte": _since,
                "$lte": _until
            },
            "hashtags": {
                "$elemMatch": {
                    "$regex": hashtag,
                    "$options": "i"
        }}}},
        {"$group": {
            "_id": {
                "day": {"$dayOfYear": "$date_published"},
                "hour": {"$hour": "$date_published"},
                **group_filter
            },
            'count': {"$sum": 1},
            "dte": {"$last": "$date_published"},
            **{k: {"$last": v} for k,v in group_filter.items()}
        }},
        {"$project": {
            "_id": 0,
            "start_hour": "$dte",
            "count": 1,
            **group_filter
    }}])

    def fix_record(adict):
        adict.update(
            start_hour=adict['start_hour'].replace(microsecond=0,second=0,minute=0)
        )
        return {**adict, "hashtag": hashtag}
    return [fix_record(item) for item in cur]


hourly_mentions_by_network_within_range = partial(
    hourly_mentions_within_range,
    group_filter={"network": "$network"}
)


def geo_mentions(collection, hashtag, level):
    if not level in ('city', 'country'):
        return {
            'error': 'Level must be one of ("city", "country"), not "{}"'.format(level)
        }
    cursor = collection.aggregate([
        {"$match": {
            "hashtags": {
                "$elemMatch": {
                    "$regex": hashtag,
                    "$options": "i"}}}},
        {"$group": {
            "_id": "${}".format(level),
            "count": {"$sum": 1}}},
        {"$project": {
            "_id": 0,
            "level": "$_id",
            "count": 1}}])
    return list(cursor)
