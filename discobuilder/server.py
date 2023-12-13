from textwrap import dedent

import yaml
from rich.prompt import Confirm, Prompt

from discobuilder import console, warning
from discobuilder.config import CONFIG
from discobuilder.adapter.git import (
    GitPullFailure,
    checkout_ref,
    clone_repo,
    commit_discovery_change,
    configure_git,
    new_private_branch,
    pull_repo,
)
from discobuilder.adapter.rhpkg import rhpkg
from discobuilder.adapter.chaski import run_chaski, set_up_chaski
from discobuilder.adapter.kerberos import kinit


def set_up_server():
    if not clone_repo(
        CONFIG.discovery_server_git_url.format(username=CONFIG.kerberos_username),
        CONFIG.discovery_server_git_repo_path,
    ):
        try:
            checkout_ref(CONFIG.discovery_server_git_repo_path, "master")
            pull_repo(CONFIG.discovery_server_git_repo_path)
        except GitPullFailure as e:
            warning(f"{e}")


def show_next_steps_summary(
    with_chaski=True, with_scratch=True, server_target="discovery-1-rhel-9"
):
    release_message = dedent(
        f"""
        [b]discovery-server[/b] should exist at:

            {CONFIG.discovery_server_git_repo_path}
        """
    )

    if with_chaski:
        chaski_command = (
            f"python3 -m poetry run -C {CONFIG.chaski_git_repo_path} chaski"
        )
        chaski_message = dedent(
            f"""
            [b]chaski[/b] can now be executed like:

                {chaski_command}

            Consider setting a shell alias for convenience:

                alias CHASKI="{chaski_command}"

            Remember to branch discovery-server and update versions with chaski. For example:

                cd {CONFIG.discovery_server_git_repo_path}
                git fetch -p --all
                git checkout {server_target}
                git checkout -b {CONFIG.private_branch_name}
                sed -i 's/^quipucords-server: 1.4.2$/quipucords-server: 1.4.3/' sources-version.yaml

                CHASKI update-remote-sources {CONFIG.discovery_server_git_repo_path}

                git commit -am 'chore: update quipucords-server 1.4.3'
                git push --set-upstream origin {CONFIG.private_branch_name}
            """
        )
        release_message += chaski_message

    if with_scratch:
        release_message += dedent(
            f"""
            Create a scratch build:

                cd {CONFIG.discovery_server_git_repo_path}
                rhpkg container-build --target={server_target}-containers-candidate --scratch
            """
        )

    release_message += dedent(
        f"""
        Update the release branch and create the release build:

            cd {CONFIG.discovery_server_git_repo_path}
            git checkout {server_target}
            git rebase {CONFIG.private_branch_name}
            git push
            rhpkg container-build --target={server_target}-containers-candidate
        """
    )
    console.rule("Suggested Next Steps")
    console.print(dedent(release_message))


def update_sources_yaml():
    with open(
        f"{CONFIG.discovery_server_git_repo_path}/sources-version.yaml", "r"
    ) as versions_file:
        sources_versions = yaml.safe_load(versions_file)
    for key, value in sources_versions.items():
        new_value = Prompt.ask(f"New value for '{key}'", default=value)
        sources_versions[key] = new_value
    with open(
        f"{CONFIG.discovery_server_git_repo_path}/sources-version.yaml", "w"
    ) as versions_file:
        versions_file.write(yaml.dump(sources_versions, Dumper=yaml.CDumper))


def build_server():
    configure_git()
    kinit()
    set_up_chaski()
    set_up_server()
    if not Confirm.ask("Want to [b]automate[/b] version updates?", default=True):
        show_next_steps_summary()
        return

    base_branch = new_private_branch(CONFIG.discovery_server_git_repo_path)
    target = base_branch.split("/")[-1]
    update_sources_yaml()
    run_chaski()
    commit_discovery_change()
    if not Confirm.ask("Want to create a [b]scratch[/b] build?", default=True):
        show_next_steps_summary(with_chaski=False, server_target=target)
        return

    rhpkg(
        command="container-build",
        scratch=True,
        target=f"{target}-containers-candidate",
        repo_path=CONFIG.discovery_server_git_repo_path,
    )
    show_next_steps_summary(with_chaski=False, with_scratch=False, server_target=target)
