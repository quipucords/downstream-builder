from rich.prompt import Confirm, Prompt

from discobuilder.adapter.git import configure_git
from discobuilder.adapter.kerberos import kinit
from discobuilder.builder.cli import build_cli  # noqa: F401
from discobuilder.builder.ctl import build_ctl  # noqa: F401


def build():
    configure_git()
    kinit()

    while True:
        choice = Prompt.ask(
            "What do you want to build?",
            choices=["cli", "ctl"],
            default="cli",
        )
        eval(f"build_{choice}()")
        if not Confirm.ask("Want to build something else?"):
            break
