import time

from scrapyd_api import ScrapydAPI


class ScrapyScheduler(object):
    def __init__(self, project_name, apis):
        self.project_name = project_name
        self._apis = {ScrapydAPI(a): [] for a in apis}

    def _renew(self):
        for api in self._apis.keys():
            self._apis[api] = api.list_jobs(self.project_name)

    def _get_least_busy(self):
        sum_load = lambda x: len(x['running']) + len(x['pending'])
        return sorted(
            self._apis.items(),
            key=lambda x: sum_load(x[1])
        )[0][0]

    def load_egg(self, eggpath):
        with open(eggpath, 'rb') as eggfile:
            for api in self._apis:
                api.add_version(self.project_name, time.time(), eggfile)
                # i think this is the proper way
                eggfile.seek(0)

    def schedule_one(self, tag_net, renew=True):
        if renew:
            self._renew()
        api = self._get_least_busy()
        ret = api.schedule(
            self.project_name,
            tag_net.network.name,
            tag_name=tag_net.hashtag.tag
        )
        self._apis[api]['pending'].append({
                'id': ret,
                'spider': tag_net.network.name
        })

    def schedule_many(self, tags):
        if not len(tags):
            return
        first, *rest = tags
        self.schedule_one(first)
        for r in rest:
            self.schedule_one(r, renew=False)

    def cancel(self, job_id):
        raise NotImplementedError("Do you really need it?")

    def cancel_all(self):
        self._renew()
        for api, load in self._apis.items():
            for item in load['running'] + load['pending']:
                api.cancel(self.project_name, item['id'])
