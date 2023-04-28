#!/usr/bin/python3
from dataclasses import dataclass
from getpass import getpass
from os import environ, path
from textwrap import dedent

from rich.console import Console
from rich.progress import Progress
from rich.prompt import Prompt

import subprocess
import sys

console = Console()


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
    discovery_git_url = environ.get(
        "DISCOVERY_GIT_URL",
        "ssh://{username}@pkgs.devel.redhat.com/containers/discovery-server.git",
    )
    discovery_git_repo_path = environ.get(
        "DISCOVERY_GIT_REPO_PATH", "/repos/discovery-server"
    )
    verbose_subprocesses = environ.get("VERBOSE_SUBPROCESSES", "0")


CONFIG = Config()

STDOUT = subprocess.DEVNULL if CONFIG.verbose_subprocesses == "0" else subprocess.STDOUT
STDERR = subprocess.DEVNULL if CONFIG.verbose_subprocesses == "0" else subprocess.STDERR


def error(message):
    console.print("[b]ERROR:[/b]", message, style="red")


def warning(message):
    console.print("[b]Warning:[/b]", message, style="orange1")


def git_config_add(key, value):
    subprocess.call(
        ["git", "config", "--global", "--add", key, value], stdout=STDOUT, stderr=STDERR
    )


def prompt_input(description, default=None, required=False):
    value = None
    while value is None or value == "":
        if not (value := Prompt.ask(description, default=default)):
            value = default
        if not required:
            break
        if required and not value:
            error(f"{description} is required")
    return value


def configure_git():
    CONFIG.name = prompt_input("git user name", CONFIG.git_name, True)
    CONFIG.email = prompt_input("git user email", CONFIG.git_email, True)
    CONFIG.signingkey = prompt_input(
        "git user signingkey", CONFIG.git_signingkey, False
    )

    git_config_add("user.name", CONFIG.name)
    git_config_add("user.email", CONFIG.email)
    if CONFIG.signingkey:
        git_config_add("user.signingkey", CONFIG.signingkey)
        git_config_add("commit.gpgsign", "true")
        warning("Don't forget to import your GPG signing key!")
    else:
        git_config_add("commit.gpgsign", "false")


def kinit():
    if subprocess.call(["klist", "-s"]) == 0:
        warning("Skipping kinit because a ticket is already present.")
        return

    success = False
    while not success:
        CONFIG.kerberos_username = prompt_input(
            "kerberos username", CONFIG.kerberos_username, True
        )
        success = subprocess.call(["kinit", CONFIG.kerberos_username]) == 0


def is_git_repo(path):
    return (
        subprocess.call(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=path,
            stdout=STDOUT,
            stderr=STDERR,
        )
        == 0
    )


def clone_repo(origin_url, local_path):
    if path.isdir(local_path):
        warning(f"Directory already exists at {local_path}.")
        if not is_git_repo(local_path):
            raise Exception(f"{local_path} is not in a git repo work tree")
        return
    if subprocess.call(["git", "clone", origin_url, local_path]) != 0:
        raise Exception("Failed to clone {origin_url} to {local_path}")


def set_up_chaski():
    clone_repo(CONFIG.chaski_git_url, CONFIG.chaski_git_repo_path)
    with Progress() as progress:
        progress.add_task("Waiting on `poetry install` for chaski", total=None)
        if (
            subprocess.call(
                ["poetry", "install", "-C", CONFIG.chaski_git_repo_path],
                stdout=STDOUT,
                stderr=STDERR,
            )
            != 0
        ):
            raise Exception(
                f"Failed to `poetry install` in {CONFIG.chaski_git_repo_path}"
            )


def set_up_discovery():
    clone_repo(
        CONFIG.discovery_git_url.format(username=CONFIG.kerberos_username),
        CONFIG.discovery_git_repo_path,
    )


def instructions():
    chaski_command = f"poetry run -C {CONFIG.chaski_git_repo_path} chaski"
    message = f"""
    [b]chaski[/b] can now be executed like:

        {chaski_command}

    Consider setting a shell alias for convenience:

        alias CHASKI="{chaski_command}"

    [b]discovery-server[/b] should exist at:

        {CONFIG.discovery_git_repo_path}

    Remember to branch, update versions, and push. For example:

        cd {CONFIG.discovery_git_repo_path}
        git fetch -p --all
        git checkout discovery-1.2-rhel-8
        git checkout -b private-{CONFIG.kerberos_username}-1.2.x
        sed -i 's/^quipucords-server: 1.2.4$/quipucords-server: 1.2.5/' sources-version.yaml

        CHASKI update-remote-sources {CONFIG.discovery_git_repo_path}

        git commit -am 'chore: update quipucords-server 1.2.5'
    """
    console.rule("Suggested Next Steps")
    console.print(dedent(message))


if __name__ == "__main__":
    if not sys.__stdin__.isatty():
        raise Exception("This script requires an interactive terminal.")
    configure_git()
    kinit()
    set_up_chaski()
    set_up_discovery()
    instructions()
