from os import path
from pathlib import Path

from rich.prompt import Confirm, Prompt
from rich.table import Table

from discobuilder import config, console, prompt_input, warning
from discobuilder.adapter.subprocess import subprocess_call, subprocess_run


class GitCloneFailure(Exception):
    pass


class GitCheckoutBFailure(Exception):
    pass


class GitCheckoutFailure(Exception):
    pass


class GitFetchAllFailure(Exception):
    pass


class GitPullFailure(Exception):
    pass


class NotAGitRepo(Exception):
    pass


def git_config_add(key, value):
    subprocess_call(
        ["git", "config", "--global", "--add", key, value],
        stdout=config.STDOUT,
        stderr=config.STDERR,
    )


def configure_git():
    config.name = prompt_input("git user name", config.GIT_NAME, True)
    config.email = prompt_input("git user email", config.GIT_EMAIL, True)
    config.signingkey = prompt_input(
        "git user signingkey", config.GIT_SIGNING_KEY, False
    )

    git_config_add("user.name", config.name)
    git_config_add("user.email", config.email)
    if config.signingkey:
        git_config_add("user.signingkey", config.signingkey)
        git_config_add("commit.gpgsign", "true")
        warning("Don't forget to import your GPG signing key!")
    else:
        git_config_add("commit.gpgsign", "false")


def is_git_repo(local_path):
    return (
        subprocess_call(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=local_path,
            stdout=config.STDOUT,
            stderr=config.STDERR,
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


def get_existing_release_branch(
    repo_path, branch_prefix_filter="", default_branch_name=None
):
    subprocess_call(
        ["git", "fetch", "-p", "--all"],
        stdout=config.STDOUT,
        stderr=config.STDERR,
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
                    name.strip()
                    for name in git_branch.stdout.decode().split("\n")
                    if name.strip().startswith(branch_prefix_filter)
                )
            )
        )
    )
    default_choice = (
        next(
            (num for num, name in branches.items() if name == default_branch_name), None
        )
        if default_branch_name
        else None
    )

    table = Table("#", "branch ref")
    for num, name in branches.items():
        table.add_row(num, name)

    console.print(table)
    kwargs = {"default": default_choice} if default_choice is not None else {}
    base_branch_key = Prompt.ask(
        "Which # release branch from the table above?",
        choices=branches.keys(),
        **kwargs,
    )
    return branches[base_branch_key]


def new_private_branch(base_branch, repo_path):
    success = subprocess_call(
        ["git", "checkout", base_branch],
        cwd=repo_path,
        stdout=config.STDOUT,
        stderr=config.STDERR,
    )
    if success != 0:
        raise GitCheckoutFailure(f"Failed `git checkout {base_branch}`")
    success = subprocess_call(
        ["git", "checkout", "-B", config.PRIVATE_BRANCH_NAME],
        cwd=repo_path,
    )
    if success != 0:
        raise GitCheckoutBFailure(
            f"Failed `git checkout -B {config.PRIVATE_BRANCH_NAME}`"
        )


def commit(repo_path, and_push=True, default_commit_message="chore: update versions"):
    # TODO check if the repo is dirty before trying to commit
    subprocess_call(["git", "diff", "HEAD"], cwd=repo_path)
    dir_name = Path(repo_path).name
    commit_message = prompt_input(
        f"git commit message for {dir_name}", default=default_commit_message
    )
    success = subprocess_call(
        [
            "git",
            "commit",
            "-am",
            commit_message,
        ],
        cwd=repo_path,
    )
    if not and_push:
        return
    if success != 0 and not Confirm.ask(
        "Failed git commit. Push anyway?", default=True
    ):
        return
    push(repo_path)


def push(repo_path):
    success = subprocess_call(
        [
            "git",
            "push",
            "--force",
            "--set-upstream",
            "origin",
            config.PRIVATE_BRANCH_NAME,
        ],
        cwd=repo_path,
    )
    if success != 0:
        raise Exception("Failed git push")
