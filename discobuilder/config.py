import time
from dataclasses import dataclass
from os import environ

import subprocess


@dataclass
class Config:
    git_name = environ.get("GIT_NAME", None)
    git_email = environ.get("GIT_EMAIL", None)
    git_signingkey = environ.get("GIT_SIGNINGKEY", None)
    kerberos_username = environ.get("KERBEROS_USERNAME", None)
    chaski_git_url = environ.get(
        "CHASKI_GIT_URL", "https://github.com/quipucords/chaski.git"
    )
    chaski_git_repo_path = environ.get("CHASKI_GIT_REPO_PATH", "/repos/chaski")
    chaski_git_committish = environ.get("CHASKI_GIT_COMMITTISH", "main")
    discovery_server_git_url = environ.get(
        "DISCOVERY_SERVER_GIT_URL",
        "ssh://{username}@pkgs.devel.redhat.com/containers/discovery-server.git",
    )  # see also: https://pkgs.devel.redhat.com/cgit/containers/discovery-server
    discovery_server_git_repo_path = environ.get(
        "DISCOVERY_SERVER_GIT_REPO_PATH", "/repos/discovery-server"
    )
    show_commands = environ.get("SHOW_COMMANDS", "0")
    verbose_subprocesses = environ.get("VERBOSE_SUBPROCESSES", "0")
    private_branch_name = f"private-{kerberos_username}-{time.time()}"


CONFIG = Config()
STDOUT = subprocess.DEVNULL if CONFIG.verbose_subprocesses == "0" else subprocess.PIPE
STDERR = subprocess.DEVNULL if CONFIG.verbose_subprocesses == "0" else subprocess.STDOUT
