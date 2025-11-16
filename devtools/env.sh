#!/bin/bash
export DOCKER_GID=$( [ "$(uname)" = "Darwin" ] && echo "0" || grep docker /etc/group | cut -d: -f3 )
export COMPOSE_PROJECT_NAME=$(basename $(basename "$(dirname "$PWD")"))
echo "project_name: $COMPOSE_PROJECT_NAME"
[ -f ".env" ] && set -a && source .env && set +a
