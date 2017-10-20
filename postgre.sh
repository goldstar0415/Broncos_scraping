#!/bin/sh

docker rm -f hashtag

docker run -d --name hashtag -v /var/work/postgres/korneev_hashtag:/var/lib/postgresql/data --env="POSTGRES_PASSWORD=blahblah" --env="POSTGRES_USER=hashtag" -p 127.0.0.1:8765:5432 mdillon/postgis:9.5
