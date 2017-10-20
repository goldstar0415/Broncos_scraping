## Basic starter guide ##

* Consider default env. variables in `.envrc` and corresponding code on the bottom of `hashtag/settings.py`. Adjust as needed.
* Start scrapyd instance. For example, you can use default config `scrapyd/1`
  `cd scrapyd/1 && scrapyd` (note the process is non-daemon by default)
** If you're willing to use many scrapyd instances or to run any of those on non-default host and port, set SCRAPYD_NODES like this: `export SCRAPYD_NODES="http://host1:port1;http://hostN:portN"`
* start scheduler: `python run.py` (it will build and deploy an egg to scrapyd instance which will cause a lot of weird stuff printed on your screen)
