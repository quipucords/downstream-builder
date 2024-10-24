from rich.progress import Progress

from discobuilder import config
from discobuilder.adapter.git import checkout_ref, clone_repo, pull_repo
from discobuilder.adapter.subprocess import subprocess_check_call, CalledProcessError


class PoetryInstallFailure(Exception):
    pass


def set_up_chaski():
    clone_repo(config.CHASKI_GIT_URL, config.CHASKI_GIT_REPO_PATH)
    checkout_ref(config.CHASKI_GIT_REPO_PATH, config.CHASKI_GIT_COMMITTISH)
    pull_repo(config.CHASKI_GIT_REPO_PATH)
    if config.VERBOSE_SUBPROCESSES:
        poetry_install_chaski()
    else:
        with Progress() as progress:
            poetry_install_chaski()
            progress.add_task("Waiting on `poetry install` for chaski", total=None)


def poetry_install_chaski():
    command = [
        "python3",
        "-m",
        "poetry",
        "install",
        "-C",
        config.CHASKI_GIT_REPO_PATH,
    ]
    kwargs = (
        {"stdout": config.STDOUT, "stderr": config.STDERR}
        if config.VERBOSE_SUBPROCESSES
        else {}
    )
    try:
        subprocess_check_call(command, **kwargs)
    except CalledProcessError:
        raise PoetryInstallFailure(
            f"Failed to `poetry install` in {config.CHASKI_GIT_REPO_PATH}"
        )


def run_chaski(distgit_path):
    subprocess_check_call(
        [
            "python3",
            "-m",
            "poetry",
            "run",
            "-C",
            config.CHASKI_GIT_REPO_PATH,
            "chaski",
            "update-remote-sources",
            distgit_path,
        ]
    )
    subprocess_check_call(
        [
            "python3",
            "-m",
            "poetry",
            "run",
            "-C",
            config.CHASKI_GIT_REPO_PATH,
            "chaski",
            "update-rust-deps",
            distgit_path,
        ]
    )
