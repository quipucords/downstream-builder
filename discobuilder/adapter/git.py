from os import path

from rich.prompt import Confirm, Prompt
from rich.table import Table

from discobuilder import console, prompt_input
from discobuilder import warning
from discobuilder.adapter.subprocess import subprocess_call, subprocess_run
from discobuilder.config import CONFIG, STDERR, STDOUT


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
        ["git", "config", "--global", "--add", key, value], stdout=STDOUT, stderr=STDERR
    )


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
