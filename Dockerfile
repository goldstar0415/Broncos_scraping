FROM python:3.6

ARG version=dev

RUN apt-get update -qq && apt-get upgrade -qq \
    && apt-get install -y --no-install-recommends \
        python3-setuptools \
        supervisor \
    && BUILD_DEPS='build-essential python3-dev git' \
    && apt-get install -y --no-install-recommends ${BUILD_DEPS}

RUN cd /usr/local/share \
	&& wget https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2 \
	&& tar xjf phantomjs-2.1.1-linux-x86_64.tar.bz2 \
	&& ln -s /usr/local/share/phantomjs-2.1.1-linux-x86_64/bin/phantomjs /usr/local/share/phantomjs \
	&& ln -s /usr/local/share/phantomjs-2.1.1-linux-x86_64/bin/phantomjs /usr/local/bin/phantomjs \
	&& ln -s /usr/local/share/phantomjs-2.1.1-linux-x86_64/bin/phantomjs /usr/bin/phantomjs

COPY supervisord.conf /etc/supervisor/supervisord.conf

ADD requirements.txt /opt/app/requirements.txt
RUN pip3 install --no-cache-dir -r /opt/app/requirements.txt

COPY run.py /opt/app/run.py
COPY scheduler.py /opt/app/scheduler.py
COPY scrapy.cfg /opt/app/scrapy.cfg
COPY builder.py /opt/app/builder.py
COPY setup.py /opt/app/setup.py

COPY scrapyd /opt/app/scrapyd
COPY hashtag /opt/app/hashtag

WORKDIR /opt/app

RUN python3 -c 'import compileall, os; compileall.compile_dir(os.curdir, force=1)' > /dev/null

RUN apt-get autoremove -y ${BUILD_DEPS} \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN mkdir -p /var/log/parser

EXPOSE 80

CMD ["supervisord", "-n","-c", "/etc/supervisor/supervisord.conf"]
