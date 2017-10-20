#!/usr/bin/env python

import json
import pika
import traceback
from pymongo import MongoClient
from bson import json_util

import aggregations
from hashtag import settings

mongo = MongoClient(settings.MONGO_URL)
collection = mongo.get_default_database()[settings.POST_TABLENAME]
channel = pika.BlockingConnection(
    pika.URLParameters(
        settings.RABBIT_URI
    )).channel()


channel.queue_declare(queue=settings.RABBIT_Q)


def do_task(payload):
    task = payload.get('task', None)
    if not task:
        return {'error': '`task` key not present'}

    func = getattr(aggregations, task, None)
    if not func:
        return {'error': 'No such task: {}'.format(task)}
    try:
        return func(collection, **payload.get('params', {}))
    except Exception:
        return {'error': 'task execution failed at: {}'.format(traceback.format_exc())}


def on_request(ch, method, props, body):
    try:
        payload = json.loads(body, object_hook=json_util.object_hook)
    except json.decoder.JSONDecodeError:
        response = {'error': 'Cannot load task as json: {}'.format(body)}
    else:
        response = do_task(payload)

    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(
                         correlation_id=props.correlation_id),
                     body=json.dumps(response, default=json_util.default))
    ch.basic_ack(delivery_tag = method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(on_request, queue=settings.RABBIT_Q)

print(" [x] Awaiting RPC requests")
channel.start_consuming()
