import subprocess
import time
from os import environ


# git user configs
GIT_NAME = environ.get("GIT_NAME", None)
GIT_EMAIL = environ.get("GIT_EMAIL", None)
GIT_SIGNING_KEY = environ.get("GIT_SIGNING_KEY", None)

# who is pushing to dist-git
KERBEROS_USERNAME = environ.get("KERBEROS_USERNAME", None)
PRIVATE_BRANCH_NAME = environ.get(
    "PRIVATE_BRANCH_NAME", f"private-{KERBEROS_USERNAME}-{time.time()}"
)

# where are my repos
# discovery-cli is downstream repo for packaging qpc
DISCOVERY_CLI_GIT_URL = environ.get(
    "DISCOVERY_CLI_GIT_URL",
    "ssh://{username}@pkgs.devel.redhat.com/rpms/discovery-cli.git",
)  # see also: https://pkgs.devel.redhat.com/cgit/rpms/discovery-cli
DISCOVERY_CLI_GIT_REPO_PATH = environ.get(
    "DISCOVERY_CLI_GIT_REPO_PATH", "/repos/discovery-cli"
)
DISCOVERY_CLI_GIT_REMOTE_RELEASE_BRANCH_DEFAULT = environ.get(
    "DISCOVERY_CLI_GIT_REMOTE_RELEASE_BRANCH_DEFAULT",
    "remotes/origin/discovery-2-rhel-9",
)
DISCOVERY_CLI_GIT_REMOTE_RELEASE_BRANCH_PREFIX = environ.get(
    "DISCOVERY_CLI_GIT_REMOTE_RELEASE_BRANCH_PREFIX", "remotes/origin/discovery-2-"
)
# discovery-installer is downstream repo for packaging quipucords-installer
DISCOVERY_INSTALLER_GIT_URL = environ.get(
    "DISCOVERY_INSTALLER_GIT_URL",
    "ssh://{username}@pkgs.devel.redhat.com/rpms/discovery-installer.git",
)  # see also: https://pkgs.devel.redhat.com/cgit/rpms/discovery-installer
QUIPUCORDS_INSTALLER_SPEC_URL = environ.get(
    "DISCOVERY_INSTALLER_UPSTREAM_SPEC_URL",
    (
        "https://raw.githubusercontent.com/quipucords/quipucords-installer/"
        "{0}/quipucords-installer.spec"
    ),
)
DISCOVERY_INSTALLER_GIT_REPO_PATH = environ.get(
    "DISCOVERY_INSTALLER_GIT_REPO_PATH", "/repos/discovery-installer"
)
DISCOVERY_INSTALLER_GIT_REMOTE_RELEASE_BRANCH_DEFAULT = environ.get(
    "DISCOVERY_INSTALLER_GIT_REMOTE_RELEASE_BRANCH_DEFAULT",
    "remotes/origin/discovery-2-rhel-9",
)
DISCOVERY_INSTALLER_GIT_REMOTE_RELEASE_BRANCH_PREFIX = environ.get(
    "DISCOVERY_INSTALLER_GIT_REMOTE_RELEASE_BRANCH_PREFIX", "remotes/origin/discovery-"
)
# discoveryctl is downstream repo for packaging quipucordsctl
DISCOVERY_CTL_GIT_URL = environ.get(
    "DISCOVERY_CTL_GIT_URL",
    "ssh://{username}@pkgs.devel.redhat.com/rpms/discoveryctl.git",
)  # see also: https://pkgs.devel.redhat.com/cgit/rpms/discoveryctl
QUIPUCORDS_CTL_SPEC_URL = environ.get(
    "DISCOVERY_CTL_UPSTREAM_SPEC_URL",
    (
        "https://raw.githubusercontent.com/quipucords/quipucordsctl/"
        "{0}/quipucordsctl.spec"
    ),
)
DISCOVERY_CTL_GIT_REPO_PATH = environ.get(
    "DISCOVERY_CTL_GIT_REPO_PATH", "/repos/discoveryctl"
)
DISCOVERY_CTL_GIT_REMOTE_RELEASE_BRANCH_DEFAULT = environ.get(
    "DISCOVERY_CTL_GIT_REMOTE_RELEASE_BRANCH_DEFAULT",
    "remotes/origin/discovery-2-rhel-9",
)
DISCOVERY_CTL_GIT_REMOTE_RELEASE_BRANCH_PREFIX = environ.get(
    "DISCOVERY_CTL_GIT_REMOTE_RELEASE_BRANCH_PREFIX", "remotes/origin/discovery-"
)

# how noisy should I be
SHOW_COMMANDS = environ.get("SHOW_COMMANDS", "0") == "1"
VERBOSE_SUBPROCESSES = environ.get("VERBOSE_SUBPROCESSES", "0") == "1"
STDOUT = subprocess.DEVNULL if not VERBOSE_SUBPROCESSES else subprocess.PIPE
STDERR = subprocess.DEVNULL if not VERBOSE_SUBPROCESSES else subprocess.STDOUT
