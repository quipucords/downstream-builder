from discobuilder import prompt_input, warning
from discobuilder.adapter.subprocess import subprocess_call
from discobuilder.config import CONFIG


def kinit():
    args = ["klist", "-s"]
    if subprocess_call(args) == 0:
        warning("Skipping kinit because a ticket is already present.")
        return

    success = False
    while not success:
        CONFIG.kerberos_username = prompt_input(
            "kerberos username", CONFIG.kerberos_username, True
        )
        success = subprocess_call(["kinit", CONFIG.kerberos_username]) == 0
