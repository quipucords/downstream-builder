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


class GitCheckoutBFailure(Exception):
    pass


class GitCheckoutFailure(Exception):
    pass


class GitCloneFailure(Exception):
    pass


class GitCloneFailure(Exception):
    pass


class GitFetchAllFailure(Exception):
    pass


class GitPullFailure(Exception):
    pass


class NotAGitRepo(Exception):
    pass


class PoetryInstallFailure(Exception):
    pass


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


def error(message):
    console.print("[b]ERROR:[/b]", message, style="red")


def warning(message):
    console.print("[b]Warning:[/b]", message, style="orange1")


def subprocess_call(*args, **kwargs):
    return subprocess_command(subprocess.call, *args, **kwargs)


def subprocess_run(*args, **kwargs):
    return subprocess_command(subprocess.run, *args, **kwargs)


def subprocess_command(command, *args, **kwargs):
    if Config.show_commands:
        console.print(f"# {command.__name__}", style="bright_black")
        for key, value in kwargs.items():
            console.print(f"# {key}: {value}", style="bright_black")
        if len(args) > 1:
            console.print(f'# {" ".join([str(arg) for arg in args[1:]])}')
        if args:
            console.print(f'[green]$[/green] {" ".join([str(arg) for arg in args[0]])}')
    return command(*args, **kwargs)


def git_config_add(key, value):
    subprocess_call(
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
    args = ["klist", "-s"]
    if subprocess_call(args) == 0:
        warning("Skipping kinit because a ticket is already present.")
        return

    success = False
    while not success:
        CONFIG.kerberos_username = prompt_input(
            "kerberos username", CONFIG.kerberos_username, True
        )
        success = subprocess_call(["kinit", CONFIG.kerberos_username]) == 0


def is_git_repo(local_path):
    return (
        subprocess_call(
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
            raise NotAGitRepo(f"{local_path} is not in a git repo work tree")
        return False
    if subprocess_call(["git", "clone", origin_url, local_path]) != 0:
        raise GitCloneFailure(f"Failed to clone {origin_url} to {local_path}")
    return True


def checkout_ref(local_path, ref):
    if not is_git_repo(local_path):
        raise NotAGitRepo(f"{local_path} is not in a git repo work tree")
    if subprocess_call(["git", "fetch", "--all"], cwd=local_path) != 0:
        raise GitFetchAllFailure(f"Failed to fetch all for repo at {local_path}")
    if subprocess_call(["git", "checkout", ref], cwd=local_path) != 0:
        raise GitCheckoutFailure(
            f"Failed to checout ref {ref} for repo at {local_path}"
        )


def pull_repo(local_path):
    if not is_git_repo(local_path):
        raise NotAGitRepo(f"{local_path} is not in a git repo work tree")
    if subprocess_call(["git", "pull"], cwd=local_path) != 0:
        raise GitPullFailure(f"Failed to pull repo at {local_path}")


def set_up_chaski():
    clone_repo(CONFIG.chaski_git_url, CONFIG.chaski_git_repo_path)
    checkout_ref(CONFIG.chaski_git_repo_path, CONFIG.chaski_git_committish)
    pull_repo(CONFIG.chaski_git_repo_path)
    with Progress() as progress:
        progress.add_task("Waiting on `poetry install` for chaski", total=None)
        if (
            subprocess_call(
                [
                    "python3",
                    "-m",
                    "poetry",
                    "install",
                    "-C",
                    CONFIG.chaski_git_repo_path,
                ],
                stdout=STDOUT,
                stderr=STDERR,
            )
            != 0
        ):
            raise PoetryInstallFailure(
                f"Failed to `poetry install` in {CONFIG.chaski_git_repo_path}"
            )


def set_up_server():
    if not clone_repo(
        CONFIG.discovery_server_git_url.format(username=CONFIG.kerberos_username),
        CONFIG.discovery_server_git_repo_path,
    ):
        try:
            checkout_ref(CONFIG.discovery_server_git_repo_path, "master")
            pull_repo(CONFIG.discovery_server_git_repo_path)
        except GitPullFailure as e:
            warning(f"{e}")


def show_next_steps_summary(
    with_chaski=True, with_scratch=True, server_target="discovery-1-rhel-9"
):
    release_message = dedent(
        f"""
        [b]discovery-server[/b] should exist at:

            {CONFIG.discovery_server_git_repo_path}
        """
    )

    if with_chaski:
        chaski_command = (
            f"python3 -m poetry run -C {CONFIG.chaski_git_repo_path} chaski"
        )
        chaski_message = dedent(
            f"""
            [b]chaski[/b] can now be executed like:

                {chaski_command}

            Consider setting a shell alias for convenience:

                alias CHASKI="{chaski_command}"

            Remember to branch discovery-server and update versions with chaski. For example:

                cd {CONFIG.discovery_server_git_repo_path}
                git fetch -p --all
                git checkout {server_target}
                git checkout -b {CONFIG.private_branch_name}
                sed -i 's/^quipucords-server: 1.4.2$/quipucords-server: 1.4.3/' sources-version.yaml

                CHASKI update-remote-sources {CONFIG.discovery_server_git_repo_path}

                git commit -am 'chore: update quipucords-server 1.4.3'
                git push --set-upstream origin {CONFIG.private_branch_name}
            """
        )
        release_message += chaski_message

    if with_scratch:
        release_message += dedent(
            f"""
            Create a scratch build:

                cd {CONFIG.discovery_server_git_repo_path}
                rhpkg container-build --target={server_target}-containers-candidate --scratch
            """
        )

    release_message += dedent(
        f"""
        Update the release branch and create the release build:

            cd {CONFIG.discovery_server_git_repo_path}
            git checkout {server_target}
            git rebase {CONFIG.private_branch_name}
            git push
            rhpkg container-build --target={server_target}-containers-candidate
        """
    )
    console.rule("Suggested Next Steps")
    console.print(dedent(release_message))


def get_existing_release_branch(repo_path):
    subprocess_call(
        ["git", "fetch", "-p", "--all"],
        stdout=STDOUT,
        stderr=STDERR,
        cwd=repo_path,
    )
    git_branch = subprocess_run(
        ["git", "branch", "--list", "-a", "--color=never"],
        cwd=repo_path,
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


def new_private_branch(repo_path):
    # Returns the *base* branch name because we may need that later.
    base_branch = get_existing_release_branch(repo_path)
    success = subprocess_call(
        ["git", "checkout", base_branch],
        cwd=repo_path,
        stdout=STDOUT,
        stderr=STDERR,
    )
    if success != 0:
        raise GitCheckoutFailure(f"Failed `git checkout {base_branch}`")
    success = subprocess_call(
        ["git", "checkout", "-b", CONFIG.private_branch_name],
        cwd=repo_path,
    )
    if success != 0:
        raise GitCheckoutBFailure(
            f"Failed `git checkout -b {CONFIG.private_branch_name}`"
        )
    return base_branch


def update_sources_yaml():
    with open(
        f"{CONFIG.discovery_server_git_repo_path}/sources-version.yaml", "r"
    ) as versions_file:
        sources_versions = yaml.safe_load(versions_file)
    for key, value in sources_versions.items():
        new_value = Prompt.ask(f"New value for '{key}'", default=value)
        sources_versions[key] = new_value
    with open(
        f"{CONFIG.discovery_server_git_repo_path}/sources-version.yaml", "w"
    ) as versions_file:
        versions_file.write(yaml.dump(sources_versions, Dumper=yaml.CDumper))


def commit_discovery_change():
    # TODO check if the repo is dirty before trying to commit
    subprocess_call(["git", "diff"], cwd=CONFIG.discovery_server_git_repo_path)
    commit_message = prompt_input(
        "git commit message for discovery-server", default="chore: update versions"
    )
    success = subprocess_call(
        [
            "git",
            "commit",
            "-am",
            commit_message,
        ],
        cwd=CONFIG.discovery_server_git_repo_path,
    )
    if success != 0 and not Confirm.ask(
        "Failed git commit. Push anyway?", default=True
    ):
        return

    success = subprocess_call(
        ["git", "push", "--set-upstream", "origin", CONFIG.private_branch_name],
        cwd=CONFIG.discovery_server_git_repo_path,
    )
    if success != 0:
        raise Exception("Failed git push")


def run_chaski():
    subprocess_call(
        [
            "python3",
            "-m",
            "poetry",
            "run",
            "-C",
            CONFIG.chaski_git_repo_path,
            "chaski",
            "update-remote-sources",
            CONFIG.discovery_server_git_repo_path,
        ]
    )


def rhpkg(command: str, target: str, repo_path: str, scratch=True):
    args = ["rhpkg", command, "--target", target]
    if scratch:
        args += ["--scratch"]
    subprocess_call(args, cwd=repo_path)


def build_server():
    configure_git()
    kinit()
    set_up_chaski()
    set_up_server()
    if not Confirm.ask("Want to [b]automate[/b] version updates?", default=True):
        show_next_steps_summary()
        return

    base_branch = new_private_branch(CONFIG.discovery_server_git_repo_path)
    target = base_branch.split("/")[-1]
    update_sources_yaml()
    run_chaski()
    commit_discovery_change()
    if not Confirm.ask("Want to create a [b]scratch[/b] build?", default=True):
        show_next_steps_summary(with_chaski=False, server_target=target)
        return

    rhpkg(
        command="container-build",
        scratch=True,
        target=f"{target}-containers-candidate",
        repo_path=CONFIG.discovery_server_git_repo_path,
    )
    show_next_steps_summary(with_chaski=False, with_scratch=False, server_target=target)


if __name__ == "__main__":
    if not sys.__stdin__.isatty():
        raise Exception("This script requires an interactive terminal.")
    build_server()
