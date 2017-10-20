#!/usr/bin/env python
import json
import pika
import uuid
import pytz
from bson import json_util

from hashtag import settings
from datetime import datetime, timedelta

class BasicRPC(object):
    name = 'meh'
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.URLParameters(settings.RABBIT_URI))

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.__on_response, no_ack=True,
                                   queue=self.callback_queue)

    def __on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = json.loads(body, object_hook=json_util.object_hook)

    def __call__(self, *args, **kwargs):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        pl = self.format_payload(*args, **kwargs)
        print(pl)
        self.channel.basic_publish(exchange='',
                                   routing_key=settings.RABBIT_Q,
                                   properties=pika.BasicProperties(
                                         reply_to = self.callback_queue,
                                         correlation_id = self.corr_id,
                                         ),
                                   body=pl)
        while self.response is None:
            self.connection.process_data_events()
        return self.response

    def _task_template(self, params):
        params.pop('self') # yeah, sorry
        return json.dumps({
            'task': self.name,
            'params': params
        },
        default=json_util.default)


class LatestNPosts(BasicRPC):
    name = 'latest_n_older_than'
    def format_payload(self, n, _since):
        return self._task_template(locals())

class HourlyMentions(BasicRPC):
    name = 'hourly_mentions_within_range'
    def format_payload(self, hashtag, _since, _until):
        return self._task_template(locals())

class HourlyMentionsByNetwork(BasicRPC):
    name = 'hourly_mentions_by_network_within_range'
    def format_payload(self, hashtag, _since, _until):
        return self._task_template(locals())

class GeoMentions(BasicRPC):
    name = 'geo_mentions'
    def format_payload(self, hashtag, level):
        return self._task_template(locals())

if __name__ == '__main__':
    now = datetime.now(pytz.UTC)

    print(" [x] Requesting latest(2, now())")
    response = LatestNPosts()(2, now)
    print(" [.] Got:")
    print(json.dumps(response, indent=2, default=str))

    print(" [x] Requesting hourly_mentions_within_range"
          "(#gameofthrones, now()-20 days, now()")
    response = HourlyMentions()("#gameofthrones", now-timedelta(days=5), now)
    print(" [.] Got:")
    print(json.dumps(response, indent=2, default=str))

    print(" [x] Requesting hourly_mentions_by_network_within_range"
          "(#gameofthrones, now()-20 days, now()")
    response = HourlyMentionsByNetwork()("#gameofthrones", now-timedelta(days=5), now)
    print(" [.] Got:")
    print(json.dumps(response, indent=2, default=str))

    print(" [x] Requesting geo_mentions('#gameofthrones', 'country')")
    response = GeoMentions()("#gameofthrones", 'country')
    print(" [.] Got:")
    print(json.dumps(response, indent=2, default=str))
