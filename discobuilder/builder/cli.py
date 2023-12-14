import re
from pathlib import Path

from rich.prompt import Confirm, Prompt

from discobuilder import config, warning
from discobuilder.adapter.git import (
    GitPullFailure,
    checkout_ref,
    clone_repo,
    commit,
    get_existing_release_branch,
    new_private_branch,
    pull_repo,
    push,
)
from discobuilder.adapter import rhpkg
from discobuilder.adapter.subprocess import subprocess_run


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


def update_specfile_version(specfile_path):
    with open(specfile_path, "r") as specfile:
        specfile_contents = specfile.readlines()

    version_line_match = version_line_number = None
    for version_line_number, line in enumerate(specfile_contents):
        version_line_match = re.match("^(Version:\s*)(.+)$", line)
        if version_line_match:
            break

    if not version_line_match:
        raise Exception("Version not found in spec file!")

    old_version = version_line_match.group(2)
    new_version = Prompt.ask(f"New version for spec file", default=old_version)
    if new_version == old_version:
        return False

    specfile_contents[
        version_line_number
    ] = f"{version_line_match.group(1)}{new_version}\n"
    with open(specfile_path, "w") as specfile:
        specfile.writelines(specfile_contents)
    return new_version


def build_source_rpm(specfile_path):
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


def import_source_rpm(version):
    srpms_dir = Path.home() / "rpmbuild" / "SRPMS"
    for srpm in list(srpms_dir.glob(f"discovery-cli-{version}-*.src.rpm")):
        rhpkg.srpm_import(config.DISCOVERY_CLI_GIT_REPO_PATH, srpm)
        # naively expect exactly one match
        break


def set_up_cli_repo():
    if not clone_repo(
        config.DISCOVERY_CLI_GIT_URL.format(username=config.KERBEROS_USERNAME),
        config.DISCOVERY_CLI_GIT_REPO_PATH,
    ):
        try:
            checkout_ref(config.DISCOVERY_CLI_GIT_REPO_PATH, "master")
            pull_repo(config.DISCOVERY_CLI_GIT_REPO_PATH)
        except GitPullFailure as e:
            warning(f"{e}")


def build_cli():
    purge_rpmbuild_tree()
    set_up_cli_repo()

    if not Confirm.ask("Want to [b]automate[/b] version updates?", default=True):
        # show_next_steps_summary()
        return

    base_branch = get_existing_release_branch(config.DISCOVERY_CLI_GIT_REPO_PATH)
    new_private_branch(base_branch, config.DISCOVERY_CLI_GIT_REPO_PATH)
    target_name = base_branch.split("/")[-1]  # maybe not strictly true but good enough

    specfile_path = Path(f"{config.DISCOVERY_CLI_GIT_REPO_PATH}/discovery-cli.spec")
    if new_version := update_specfile_version(specfile_path):
        commit(
            config.DISCOVERY_CLI_GIT_REPO_PATH,
            default_commit_message=f"chore: update version to {new_version}",
            and_push=False,
        )
    build_source_rpm(specfile_path)
    import_source_rpm(new_version)
    commit(
        config.DISCOVERY_CLI_GIT_REPO_PATH,
        default_commit_message="chore: update sources",
        and_push=True,
    )

    if not Confirm.ask("Want to create a [b]scratch[/b] build?", default=True):
        # show_next_steps_summary(with_chaski=False, server_target=target_name)
        return

    release = Prompt.ask(f"What rhpkg '--release' value?", default="rhel-9")
    rhpkg.build(
        scratch=True,
        release=release,
        target=f"{target_name}-candidate",
        repo_path=config.DISCOVERY_CLI_GIT_REPO_PATH,
    )
