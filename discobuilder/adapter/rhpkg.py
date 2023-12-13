from discobuilder.adapter.subprocess import subprocess_call


def rhpkg(command: str, target: str, repo_path: str, scratch=True):
    args = ["rhpkg", command, "--target", target]
    if scratch:
        args += ["--scratch"]
    subprocess_call(args, cwd=repo_path)
