#!/bin/bash

if [ -n "$GIT_USER" ] && [ -n "$GIT_REPO" ]; then
    [ -d "$GIT_REPO" ] && (cd "$GIT_REPO" && git pull) || git clone "https://github.com/$GIT_USER/$GIT_REPO.git"
    git submodule update --init --recursive
fi
cd ${WORK_DIR:-.}
[ -f "init.sh" ] && ./init.sh

# Signal that entrypoint setup is complete
touch /tmp/entrypoint-ready

$@
