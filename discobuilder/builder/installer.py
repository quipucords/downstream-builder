# TODO: Refactor/deduplicate a lot of similar code between this and ./cli.py.
from textwrap import dedent

import re
from pathlib import Path

import requests
from rich.prompt import Confirm, Prompt

from discobuilder import config, console, warning
from discobuilder.adapter import git
from discobuilder.adapter import rhpkg, rpmbuild


def update_specfile_from_upstream(specfile_path: Path):
    quipucords_committish = Prompt.ask(
        "Pull from what quipucords-installer committish?", default="main"
    )
    url = config.QUIPUCORDS_INSTALLER_SPEC_URL.format(quipucords_committish)
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Unexpected status {response.status_code} downloading {url}")
    with specfile_path.open("w") as f:
        f.writelines(response.text)


def update_specfile_globals(spec_globals: list[str], specfile_path: Path):
    """
    Prompt for changes to %global values and update the spec file accordingly.

    This is a destructive operation and will rewrite the spec file contents.
    """
    with specfile_path.open("r") as specfile:
        specfile_lines = specfile.readlines()

    patterns = {
        spec_global: rf"^(%global {spec_global} )(\S*)" for spec_global in spec_globals
    }
    prompts = {
        spec_global: f"Enter '{spec_global}' value" for spec_global in spec_globals
    }
    new_values = {}
    dirty = False

    for line_number, line in enumerate(specfile_lines):
        for spec_global in spec_globals:
            if line_match := re.match(patterns[spec_global], line):
                old_value = line_match.group(2)
                new_value = Prompt.ask(prompts[spec_global], default=old_value)
                specfile_lines[line_number] = f"{line_match.group(1)}{new_value}\n"
                new_values[spec_global] = new_value
                dirty = True
                continue  # only one match should be possible per line

    if dirty:
        with specfile_path.open("w") as specfile:
            specfile.writelines(specfile_lines)

    return new_values, dirty


def import_source_rpm(version):
    srpms_dir = rpmbuild.get_srpms_path()
    for srpm in list(srpms_dir.glob(f"discovery-installer-{version}-*.src.rpm")):
        rhpkg.srpm_import(config.DISCOVERY_INSTALLER_GIT_REPO_PATH, srpm)
        # naively expect exactly one match
        return
    raise Exception(
        f"No SRPMs found? ({srpms_dir}/discovery-installer-{version}-*.src.rpm)"
    )


def set_up_repo():
    if not git.clone_repo(
        config.DISCOVERY_INSTALLER_GIT_URL.format(username=config.KERBEROS_USERNAME),
        config.DISCOVERY_INSTALLER_GIT_REPO_PATH,
    ):
        try:
            git.checkout_ref(config.DISCOVERY_INSTALLER_GIT_REPO_PATH, "master")
            git.pull_repo(config.DISCOVERY_INSTALLER_GIT_REPO_PATH)
        except git.GitPullFailure as e:
            warning(f"{e}")


def build_installer():
    rpmbuild.purge_rpmbuild_tree()
    set_up_repo()

    if not Confirm.ask("Want to [b]automate[/b] version updates?", default=True):
        show_next_steps_summary(with_scratch=True)
        return

    base_branch = git.get_existing_release_branch(
        config.DISCOVERY_INSTALLER_GIT_REPO_PATH,
        config.DISCOVERY_INSTALLER_GIT_REMOTE_RELEASE_BRANCH_PREFIX,
        config.DISCOVERY_INSTALLER_GIT_REMOTE_RELEASE_BRANCH_DEFAULT,
    )
    git.new_private_branch(base_branch, config.DISCOVERY_INSTALLER_GIT_REPO_PATH)
    target_name = base_branch.split("/")[-1]  # maybe not strictly true but good enough

    specfile_path = Path(
        f"{config.DISCOVERY_INSTALLER_GIT_REPO_PATH}/discovery-installer.spec"
    )

    if refreshed := Confirm.ask(
        "Refresh the spec file from [b]upstream[/b]?", default=True
    ):
        update_specfile_from_upstream(specfile_path)

    spec_globals = [
        "product_name_lower",
        "product_name_title",
        "version_installer",
        "server_image",
        "ui_image",
    ]
    new_spec_globals, updated = update_specfile_globals(spec_globals, specfile_path)

    if refreshed or updated:
        new_version = new_spec_globals["version_installer"]
        git.add(config.DISCOVERY_INSTALLER_GIT_REPO_PATH, specfile_path)
        git.commit(
            config.DISCOVERY_INSTALLER_GIT_REPO_PATH,
            default_commit_message=(
                f"build: update discovery-installer to {new_version}"
            ),
            and_push=False,
        )
        rpmbuild.build_source_rpm(specfile_path)
        import_source_rpm(new_version)
        git.commit(
            config.DISCOVERY_INSTALLER_GIT_REPO_PATH,
            default_commit_message="build: update sources",
            and_push=False,
        )
    git.push(config.DISCOVERY_INSTALLER_GIT_REPO_PATH)

    if not Confirm.ask("Want to create a [b]scratch[/b] build?", default=True):
        show_next_steps_summary(with_scratch=True)
        return

    release = Prompt.ask("What rhpkg '--release' value?", default="rhel-9")
    target = f"{target_name}-candidate"
    rhpkg.build(
        scratch=True,
        release=release,
        target=target,
        repo_path=config.DISCOVERY_INSTALLER_GIT_REPO_PATH,
    )

    show_next_steps_summary(with_scratch=False, release=release, target=target)


def show_next_steps_summary(with_scratch=True, release="rhel-9", target=None):
    if not target:
        target = f"discovery-1-{release}-candidate"

    release_message = dedent(
        f"""
        [b]discovery-installer[/b] should exist at:

            {config.DISCOVERY_INSTALLER_GIT_REPO_PATH}
        """
    )

    if with_scratch:
        release_message += dedent(
            f"""
            Create a scratch build:

                cd {config.DISCOVERY_INSTALLER_GIT_REPO_PATH}
                rhpkg build --release {release} --target={target} --scratch
            """
        )

    release_message += dedent(
        f"""
        Update the release branch and create the release build:

            cd {config.DISCOVERY_INSTALLER_GIT_REPO_PATH}
            git checkout discovery-1-{release}
            git rebase {config.PRIVATE_BRANCH_NAME}
            git push
            rhpkg build --scratch
            rhpkg build

        Note that `--release` and `--target` arguments are not required when you invoke `rhpkg build` from the release branches.

        Then repeat all of these steps for any other RHEL build releases (`rhel-9`, `rhel-8`).
        """
    )
    console.rule("Suggested Next Steps")
    console.print(dedent(release_message))
