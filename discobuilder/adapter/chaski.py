from rich.progress import Progress

from discobuilder import config
from discobuilder.adapter.git import checkout_ref, clone_repo, pull_repo
from discobuilder.adapter.subprocess import subprocess_call


class PoetryInstallFailure(Exception):
    pass


def set_up_chaski():
    clone_repo(config.CHASKI_GIT_URL, config.CHASKI_GIT_REPO_PATH)
    checkout_ref(config.CHASKI_GIT_REPO_PATH, config.CHASKI_GIT_COMMITTISH)
    pull_repo(config.CHASKI_GIT_REPO_PATH)
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
                    config.CHASKI_GIT_REPO_PATH,
                ],
                stdout=config.STDOUT,
                stderr=config.STDERR,
            )
            != 0
        ):
            raise PoetryInstallFailure(
                f"Failed to `poetry install` in {config.CHASKI_GIT_REPO_PATH}"
            )


def run_chaski():
    subprocess_call(
        [
            "python3",
            "-m",
            "poetry",
            "run",
            "-C",
            config.CHASKI_GIT_REPO_PATH,
            "chaski",
            "update-remote-sources",
            config.DISCOVERY_SERVER_GIT_REPO_PATH,
        ]
    )
