from math import floor
import time

def noneget_in(adict, keys, default=''):
    """
    It works like a regular get-in, but also
    returns default when `bool(down)` is False (ex.: None)
    """
    k, *ks = keys
    if isinstance(adict, (list, tuple, set)):
        if len(adict) > k:
            down = adict[k]
        else:
            down=None
    else:
        down = adict.get(k)
    if down and ks:
        return noneget_in(down, ks, default)
    elif down:
        return down
    else:
        return default


def dog_sleep(sec, step=0.1):
    [time.sleep(step) for _ in range(floor(sec/step))]


def get_first(_from, selector_fn):
    for x in _from:
        if selector_fn(x):
            return x


# class ResponseMock(object):
#     def __init__(self, url):
#         self.url = url
