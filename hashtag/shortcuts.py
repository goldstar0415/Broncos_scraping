from datetime import datetime

import pytz
from python_anticaptcha import ImageToTextTask


def unow_tz():
    return datetime.now(pytz.UTC)


def captcha_to_text(client, image_name):
    with open(image_name, 'rb') as fp:
        task = ImageToTextTask(fp)
        job = client.createTask(task)
        job.join()
        return job.get_captcha_text()
