#!/bin/sh
mkdir -p ./.ch/data
mkdir -p ./.ch/logs
docker run -d \
    -p 8123:8123 \
    -v $(realpath ./.ch/data):/var/lib/clickhouse/ \
    -v $(realpath ./.ch/logs):/var/log/clickhouse-server/ \
    --name ckangpt-clickhouse-server --ulimit nofile=262144:262144 clickhouse/clickhouse-server
