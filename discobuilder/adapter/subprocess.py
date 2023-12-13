import subprocess

from discobuilder import console
from discobuilder.config import Config


def subprocess_call(*args, **kwargs):
    """Execute command and return its return code/status."""
    return subprocess_command(subprocess.call, *args, **kwargs)


def subprocess_run(*args, **kwargs):
    """Execute command and return a CompletedProcess instance."""
    return subprocess_command(subprocess.run, *args, **kwargs)


def subprocess_command(command, *args, **kwargs):
    if Config.show_commands:
        console.print(f"# {command.__name__}", style="bright_black")
        for key, value in kwargs.items():
            console.print(f"# {key}: {value}", style="bright_black")
        if len(args) > 1:
            console.print(f'# {" ".join([str(arg) for arg in args[1:]])}')
        if args:
            console.print(f'[green]$[/green] {" ".join([str(arg) for arg in args[0]])}')
    return command(*args, **kwargs)
