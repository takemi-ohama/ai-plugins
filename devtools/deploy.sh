#!/bin/bash
source env.sh

docker compose stop -t0
docker compose up -d --scale dev=2
(sleep 5 && docker compose cp .env dev:${WORK_DIR}/.env) &
