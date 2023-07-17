#!/usr/bin/python3
from dataclasses import dataclass
from os import environ, path
from textwrap import dedent

from rich.console import Console
from rich.progress import Progress
from rich.prompt import Confirm, Prompt
from rich.table import Table

import subprocess
import sys
import time

import yaml

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
    private_branch_name = f"private-{kerberos_username}-{time.time()}"


CONFIG = Config()

STDOUT = subprocess.DEVNULL if CONFIG.verbose_subprocesses == "0" else subprocess.PIPE
STDERR = subprocess.DEVNULL if CONFIG.verbose_subprocesses == "0" else subprocess.STDOUT


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


def is_git_repo(local_path):
    return (
        subprocess.call(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=local_path,
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
        return False
    if subprocess.call(["git", "clone", origin_url, local_path]) != 0:
        raise Exception(f"Failed to clone {origin_url} to {local_path}")
    return True


def pull_repo(local_path):
    if not is_git_repo(local_path):
        raise Exception(f"{local_path} is not in a git repo work tree")
    if subprocess.call(["git", "pull"], cwd=local_path) != 0:
        raise Exception(f"Failed to pull repo at {local_path}")


def set_up_chaski():
    if not clone_repo(CONFIG.chaski_git_url, CONFIG.chaski_git_repo_path):
        pull_repo(CONFIG.chaski_git_repo_path)
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
    if not clone_repo(
        CONFIG.discovery_git_url.format(username=CONFIG.kerberos_username),
        CONFIG.discovery_git_repo_path,
    ):
        pull_repo(CONFIG.discovery_git_repo_path)


def show_next_steps_summary(with_chaski=True):
    release_message = dedent(
        f"""
        [b]discovery-server[/b] should exist at:

            {CONFIG.discovery_git_repo_path}

        """
    )

    if with_chaski:
        chaski_command = f"poetry run -C {CONFIG.chaski_git_repo_path} chaski"
        chaski_message = dedent(
            f"""
            [b]chaski[/b] can now be executed like:

                {chaski_command}

            Consider setting a shell alias for convenience:

                alias CHASKI="{chaski_command}"

            Remember to branch discovery-server and update versions with chaski. For example:

                cd {CONFIG.discovery_git_repo_path}
                git fetch -p --all
                git checkout discovery-1.2-rhel-8
                git checkout -b {CONFIG.private_branch_name}
                sed -i 's/^quipucords-server: 1.2.4$/quipucords-server: 1.2.5/' sources-version.yaml

                CHASKI update-remote-sources {CONFIG.discovery_git_repo_path}

                git commit -am 'chore: update quipucords-server 1.2.5'
                cd push --set-upstream origin {CONFIG.private_branch_name}

            """
        )
        release_message += chaski_message

    release_message += dedent(
        f"""
        rhpkg --scratch build, update the release branch, and rhpkg (no scratch):

            cd {CONFIG.discovery_git_repo_path}
            rhpkg container-build --target=discovery-1.2-rhel-8-containers-candidate --scratch
            git checkout discovery-1.2-rhel-8
            git rebase {CONFIG.private_branch_name}
            git push
            rhpkg container-build --target=discovery-1.2-rhel-8-containers-candidate

        """
    )
    console.rule("Suggested Next Steps")
    console.print(dedent(release_message))


def get_discovery_release_branch():
    subprocess.call(
        ["git", "fetch", "-p", "--all"],
        stdout=STDOUT,
        stderr=STDERR,
        cwd=CONFIG.discovery_git_repo_path,
    )
    git_branch = subprocess.run(
        ["git", "branch", "--list", "-a", "--color=never"],
        cwd=CONFIG.discovery_git_repo_path,
        capture_output=True,
    )
    branches = dict(
        (
            (str(num), name)
            for num, name in enumerate(
                sorted(
                    l.strip()
                    for l in git_branch.stdout.decode().split("\n")
                    if l.strip().startswith("remotes/origin/discovery-")
                )
            )
        )
    )

    table = Table("#", "branch ref")
    for num, name in branches.items():
        table.add_row(num, name)

    console.print(table)
    base_branch_key = Prompt.ask(
        "Which # release branch from the table above?", choices=branches.keys()
    )
    return branches[base_branch_key]


def new_discovery_branch():
    base_branch = get_discovery_release_branch()
    success = subprocess.call(
        ["git", "checkout", base_branch],
        cwd=CONFIG.discovery_git_repo_path,
        stdout=STDOUT,
        stderr=STDERR,
    )
    if success != 0:
        raise Exception(f"Failed `git checkout {base_branch}`")
    success = subprocess.call(
        ["git", "checkout", "-b", CONFIG.private_branch_name],
        cwd=CONFIG.discovery_git_repo_path,
    )
    if success != 0:
        raise Exception(f"Failed `git checkout -b {CONFIG.private_branch_name}`")


def update_sources_versions():
    with open(
        f"{CONFIG.discovery_git_repo_path}/sources-version.yaml", "r"
    ) as versions_file:
        sources_versions = yaml.safe_load(versions_file)
    for key, value in sources_versions.items():
        new_value = Prompt.ask(f"New value for '{key}'", default=value)
        sources_versions[key] = new_value
    with open(
        f"{CONFIG.discovery_git_repo_path}/sources-version.yaml", "w"
    ) as versions_file:
        versions_file.write(yaml.dump(sources_versions, Dumper=yaml.CDumper))


def commit_discovery_change():
    subprocess.call(["git", "diff"], cwd=CONFIG.discovery_git_repo_path)
    commit_message = prompt_input(
        "git commit message for discovery-server", default="chore: update versions"
    )
    success = subprocess.call(
        [
            "git",
            "commit",
            "-am",
            commit_message,
        ],
        cwd=CONFIG.discovery_git_repo_path,
    )
    if success != 0:
        raise Exception("Failed git commit")

    success = subprocess.call(
        ["git", "push", "--set-upstream", "origin", CONFIG.private_branch_name],
        cwd=CONFIG.discovery_git_repo_path,
    )
    if success != 0:
        raise Exception("Failed git push")


def update_versions():
    new_discovery_branch()
    update_sources_versions()


def run_chaski():
    subprocess.call(
        [
            "poetry",
            "run",
            "-C",
            CONFIG.chaski_git_repo_path,
            "chaski",
            "update-remote-sources",
            CONFIG.discovery_git_repo_path,
        ]
    )


if __name__ == "__main__":
    if not sys.__stdin__.isatty():
        raise Exception("This script requires an interactive terminal.")
    configure_git()
    kinit()
    set_up_chaski()
    set_up_discovery()
    if Confirm.ask("Want to [b]automate[/b] version updates?"):
        update_versions()
        run_chaski()
        commit_discovery_change()
        show_next_steps_summary(with_chaski=False)
    else:
        show_next_steps_summary()
