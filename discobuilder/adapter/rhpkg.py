from discobuilder.adapter.subprocess import subprocess_call


def rhpkg(
    command: str, repo_path: str, target: str = None, scratch=True, release: str = None
):
    args = ["rhpkg"]
    if release:
        args += ["--release", release]
    args += [command]
    if target:
        args += ["--target", target]
    if scratch:
        args += ["--scratch"]
    subprocess_call(args, cwd=repo_path)
