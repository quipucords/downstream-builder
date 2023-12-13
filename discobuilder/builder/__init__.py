from rich.prompt import Prompt

from discobuilder.adapter.git import configure_git
from discobuilder.adapter.kerberos import kinit
from discobuilder.builder.cli import build_cli
from discobuilder.builder.server import build_server


def build():
    configure_git()
    kinit()

    choice = Prompt.ask(
        "What do you want to build?", choices=["server", "cli"], default="server"
    )
    eval(f"build_{choice}()")
