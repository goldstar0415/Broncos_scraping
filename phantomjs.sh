#!/bin/sh

docker rm -f phantomjs

docker run -d --name phantomjs -p 4444:4444 wernight/phantomjs:2.0 phantomjs --webdriver=4444
