from textwrap import dedent

import yaml
from rich.prompt import Confirm, Prompt

from discobuilder import config, console, warning
from discobuilder.adapter.chaski import run_chaski, set_up_chaski
from discobuilder.adapter.git import (
    GitPullFailure,
    checkout_ref,
    clone_repo,
    commit,
    get_existing_release_branch,
    new_private_branch,
    pull_repo,
)
from discobuilder.adapter import rhpkg


def set_up_server_repo():
    if not clone_repo(
        config.DISCOVERY_SERVER_GIT_URL.format(username=config.KERBEROS_USERNAME),
        config.DISCOVERY_SERVER_GIT_REPO_PATH,
    ):
        try:
            checkout_ref(config.DISCOVERY_SERVER_GIT_REPO_PATH, "master")
            pull_repo(config.DISCOVERY_SERVER_GIT_REPO_PATH)
        except GitPullFailure as e:
            warning(f"{e}")


def show_next_steps_summary(
    with_chaski=True, with_scratch=True, server_target="discovery-1-rhel-9"
):
    release_message = dedent(
        f"""
        [b]discovery-server[/b] should exist at:

            {config.DISCOVERY_SERVER_GIT_REPO_PATH}
        """
    )

    if with_chaski:
        chaski_command = (
            f"python3 -m poetry run -C {config.CHASKI_GIT_REPO_PATH} chaski"
        )
        chaski_message = dedent(
            f"""
            [b]chaski[/b] can now be executed like:

                {chaski_command}

            Consider setting a shell alias for convenience:

                alias CHASKI="{chaski_command}"

            Remember to branch discovery-server and update versions with chaski. For example:

                cd {config.DISCOVERY_SERVER_GIT_REPO_PATH}
                git fetch -p --all
                git checkout {server_target}
                git checkout -b {config.PRIVATE_BRANCH_NAME}
                sed -i 's/^quipucords-server: 1.4.2$/quipucords-server: 1.4.3/' sources-version.yaml

                CHASKI update-remote-sources {config.DISCOVERY_SERVER_GIT_REPO_PATH}

                git commit -am 'build: update quipucords-server 1.4.3'
                git push --set-upstream origin {config.PRIVATE_BRANCH_NAME}
            """
        )
        release_message += chaski_message

    if with_scratch:
        release_message += dedent(
            f"""
            Create a scratch build:

                cd {config.DISCOVERY_SERVER_GIT_REPO_PATH}
                rhpkg container-build --target={server_target}-containers-candidate --scratch
            """
        )

    release_message += dedent(
        f"""
        Update the release branch and create the release build:

            cd {config.DISCOVERY_SERVER_GIT_REPO_PATH}
            git checkout {server_target}
            git rebase {config.PRIVATE_BRANCH_NAME}
            git push
            rhpkg container-build --target={server_target}-containers-candidate
        """
    )
    console.rule("Suggested Next Steps")
    console.print(dedent(release_message))


def update_sources_yaml():
    with open(
        f"{config.DISCOVERY_SERVER_GIT_REPO_PATH}/sources-version.yaml", "r"
    ) as versions_file:
        sources_versions = yaml.safe_load(versions_file)
    for key, value in sources_versions.items():
        new_value = Prompt.ask(f"New value for '{key}'", default=value)
        sources_versions[key] = new_value
    with open(
        f"{config.DISCOVERY_SERVER_GIT_REPO_PATH}/sources-version.yaml", "w"
    ) as versions_file:
        versions_file.write(yaml.dump(sources_versions, Dumper=yaml.CDumper))


def build_server():
    set_up_chaski()
    set_up_server_repo()
    if not Confirm.ask("Want to [b]automate[/b] version updates?", default=True):
        show_next_steps_summary()
        return

    base_branch = get_existing_release_branch(
        config.DISCOVERY_SERVER_GIT_REPO_PATH,
        config.DISCOVERY_SERVER_GIT_REMOTE_RELEASE_BRANCH_PREFIX,
        config.DISCOVERY_SERVER_GIT_REMOTE_RELEASE_BRANCH_DEFAULT,
    )
    new_private_branch(base_branch, config.DISCOVERY_SERVER_GIT_REPO_PATH)
    target_name = base_branch.split("/")[-1]  # maybe not strictly true but good enough
    update_sources_yaml()
    run_chaski(config.DISCOVERY_SERVER_GIT_REPO_PATH)
    commit(config.DISCOVERY_SERVER_GIT_REPO_PATH)
    if not Confirm.ask("Want to create a [b]scratch[/b] build?", default=True):
        show_next_steps_summary(with_chaski=False, server_target=target_name)
        return

    rhpkg.container_build(
        repo_path=config.DISCOVERY_SERVER_GIT_REPO_PATH,
        scratch=True,
        target=f"{target_name}-containers-candidate",
    )
    show_next_steps_summary(
        with_chaski=False, with_scratch=False, server_target=target_name
    )
