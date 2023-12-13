from rich.progress import Progress

from discobuilder.adapter.git import checkout_ref, clone_repo, pull_repo
from discobuilder.adapter.subprocess import subprocess_call
from discobuilder.config import CONFIG, STDERR, STDOUT


class PoetryInstallFailure(Exception):
    pass


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
