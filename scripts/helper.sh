#!/bin/bash --init-file

export GIT_NAME
export GIT_EMAIL
export GIT_SIGNINGKEY
export KERBEROS_USERNAME
export CHASKI_GIT_URL
export CHASKI_GIT_REPO_PATH
export CHASKI_GIT_COMMITTISH
export DISCOVERY_GIT_URL
export DISCOVERY_GIT_REPO_PATH
export POETRY_CACHE_DIR
export VERBOSE_SUBPROCESSES

mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "$KNOWN_HOSTS" >> ~/.ssh/known_hosts
chmod 644 ~/.ssh/known_hosts

/usr/bin/python3 -m discobuilder
