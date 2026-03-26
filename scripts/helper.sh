#!/bin/bash --init-file

export GIT_NAME
export GIT_EMAIL
export GIT_SIGNINGKEY
export KERBEROS_USERNAME
export DISCOVERY_CLI_GIT_URL
export DISCOVERY_CLI_GIT_REPO_PATH
export VERBOSE_SUBPROCESSES

mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "$KNOWN_HOSTS" >> ~/.ssh/known_hosts
chmod 644 ~/.ssh/known_hosts

/usr/bin/python3 -m discobuilder
