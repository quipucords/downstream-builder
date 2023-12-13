import subprocess
import time
from os import environ


GIT_NAME = environ.get("GIT_NAME", None)
GIT_EMAIL = environ.get("GIT_EMAIL", None)
GIT_SIGNINGKEY = environ.get("GIT_SIGNINGKEY", None)
KERBEROS_USERNAME = environ.get("KERBEROS_USERNAME", None)
CHASKI_GIT_URL = environ.get(
    "CHASKI_GIT_URL", "https://github.com/quipucords/chaski.git"
)
CHASKI_GIT_REPO_PATH = environ.get("CHASKI_GIT_REPO_PATH", "/repos/chaski")
CHASKI_GIT_COMMITTISH = environ.get("CHASKI_GIT_COMMITTISH", "main")
DISCOVERY_SERVER_GIT_URL = environ.get(
    "DISCOVERY_SERVER_GIT_URL",
    "ssh://{username}@pkgs.devel.redhat.com/containers/discovery-server.git",
)  # see also: https://pkgs.devel.redhat.com/cgit/containers/discovery-server
DISCOVERY_SERVER_GIT_REPO_PATH = environ.get(
    "DISCOVERY_SERVER_GIT_REPO_PATH", "/repos/discovery-server"
)
SHOW_COMMANDS = environ.get("SHOW_COMMANDS", "0")
VERBOSE_SUBPROCESSES = environ.get("VERBOSE_SUBPROCESSES", "0")
PRIVATE_BRANCH_NAME = f"private-{KERBEROS_USERNAME}-{time.time()}"


STDOUT = subprocess.DEVNULL if VERBOSE_SUBPROCESSES == "0" else subprocess.PIPE
STDERR = subprocess.DEVNULL if VERBOSE_SUBPROCESSES == "0" else subprocess.STDOUT
