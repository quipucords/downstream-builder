from discobuilder import config
from discobuilder.adapter.subprocess import subprocess_call


def build(repo_path, target: str = None, release: str = None, scratch=True):
    """Calls `rhpkg build` for an RPM."""
    args = ["rhpkg"]
    if release:
        args += ["--release", release]
    args += ["build"]
    if target:
        args += ["--target", target]
    if scratch:
        args += ["--scratch"]
    subprocess_call(args, cwd=repo_path)


def container_build(repo_path, target: str = None, scratch=True):
    """Calls `rhpkg container-build` for an OCI container image."""
    args = ["rhpkg", "container-build"]
    if target:
        args += ["--target", target]
    if scratch:
        args += ["--scratch"]
    subprocess_call(args, cwd=repo_path)


def srpm_import(repo_path, srpm_path):
    """Calls `rhpkg import` to update `sources` file with SRPM info."""
    subprocess_call(
        ["rhpkg", "import", srpm_path],
        cwd=repo_path,
        stdout=config.STDOUT,
        stderr=config.STDERR,
    )
