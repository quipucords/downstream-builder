#!/bin/bash --init-file

export GIT_NAME
export GIT_EMAIL
export GIT_SIGNINGKEY
export KERBEROS_USERNAME
export CHASKI_GIT_URL
export CHASKI_GIT_REPO_PATH
export DISCOVERY_GIT_URL
export DISCOVERY_GIT_REPO_PATH
export POETRY_CACHE_DIR
export VERBOSE_SUBPROCESSES

/usr/bin/python3 /helper.py
