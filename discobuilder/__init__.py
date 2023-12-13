from rich.console import Console
from rich.prompt import Prompt

console = Console()


def error(message):
    console.print("[b]ERROR:[/b]", message, style="red")


def warning(message):
    console.print("[b]Warning:[/b]", message, style="orange1")


def prompt_input(description, default=None, required=False):
    value = None
    while value is None or value == "":
        if not (value := Prompt.ask(description, default=default)):
            value = default
        if not required:
            break
        if required and not value:
            error(f"{description} is required")
    return value
