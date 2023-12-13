from discobuilder import config, prompt_input, warning
from discobuilder.adapter.subprocess import subprocess_call


def kinit():
    args = ["klist", "-s"]
    if subprocess_call(args) == 0:
        warning("Skipping kinit because a ticket is already present.")
        return

    success = False
    while not success:
        config.KERBEROS_USERNAME = prompt_input(
            "kerberos username", config.KERBEROS_USERNAME, True
        )
        success = subprocess_call(["kinit", config.KERBEROS_USERNAME]) == 0
