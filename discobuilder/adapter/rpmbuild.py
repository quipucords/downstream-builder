from pathlib import Path

from discobuilder.adapter.subprocess import subprocess_run
from discobuilder import config


def get_srpms_path() -> Path:
    return Path.home() / "rpmbuild" / "SRPMS"


def purge_rpmbuild_tree():
    subprocess_run(["rpmdev-setuptree"])
    subprocess_run(
        [
            "find",
            Path.home() / "rpmbuild",
            "-type",
            "f",
            "-printf",
            "deleted '%p'\\n",
            "-delete",
        ],
    )


def build_source_rpm(specfile_path: Path):
    subprocess_run(
        ["spectool", "--sourcedir", "--get-files", specfile_path],
        stdout=config.STDOUT,
        stderr=config.STDERR,
    )
    subprocess_run(
        ["rpmbuild", "-bs", specfile_path, "--verbose", "--clean"],
        stdout=config.STDOUT,
        stderr=config.STDERR,
    )
