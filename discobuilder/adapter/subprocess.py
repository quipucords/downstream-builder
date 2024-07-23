from subprocess import call, run, check_call, CalledProcessError

from discobuilder import config, console


def subprocess_call(*args, **kwargs):
    """Execute command and return its return code/status."""
    return subprocess_command(call, *args, **kwargs)


def subprocess_run(*args, **kwargs):
    """Execute command and return a CompletedProcess instance."""
    return subprocess_command(run, *args, **kwargs)


def subprocess_check_call(*args, **kwargs):
    """Execute command and raise CalledProcessError upon non-zero exit."""
    return subprocess_command(check_call, *args, **kwargs)


def subprocess_command(command, *args, **kwargs):
    if config.SHOW_COMMANDS:
        console.print(f"# {command.__name__}", style="bright_black")
        for key, value in kwargs.items():
            console.print(f"# {key}: {value}", style="bright_black")
        if len(args) > 1:
            console.print(f'# {" ".join([str(arg) for arg in args[1:]])}')
        if args:
            console.print(f'[green]$[/green] {" ".join([str(arg) for arg in args[0]])}')
    return command(*args, **kwargs)
