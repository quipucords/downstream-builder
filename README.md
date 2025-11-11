# Quipucords Downstream Builder

## What is this?

This is a containerized interactive script to simplify the quipucords-to-Discovery downstream build process. This means you don't need to install `rhpkg` and `brewkoji` on your own machine or run a custom VM with them any longer!

This script can trigger container builds for quipucords (Discovery) or RPMs for qpc (discovery-cli) or quipucordsctl (discoveryctl).

## How do I use it?

Optionally create a local directory for sharing repos and virtualenv cache (this can speed up subsequent runs and allows you to access the files from your host):

```sh
mkdir repos
```

Prepare your ssh configs to mount as a volume. This is REQUIRED for running with Red Hat's internal git and build servers. Please see the `unofficial-internal-documentation` for reference values. For security reasons, this public project does not include those values.

```sh
mkdir -p ./ssh-config
# assuming a recent clone of unofficial-internal-documentation nearby
cp ../unofficial-internal-documentation/reference/dist-git-ssh-configs/config ./ssh-config/config
cp ../unofficial-internal-documentation/reference/dist-git-ssh-configs/known_hosts ./ssh-config/known_hosts
chmod 640 ./ssh-config/config
chmod 640 ./ssh-config/known_hosts
```


Optionally edit a `.env` file as needed:

```sh
cp .env-example .env
vi .env
```

Build the container image:

```sh
podman build -f Containerfile -t downstream-builder:latest .
```

Connect to the Red Hat VPN. This program communicates with several internal hosts and will fail without appropriate network access.

Run the container:

```sh
podman run \
    -v "$PWD"/repos:/repos:Z \
    -v "$PWD"/ssh-config:/home/builder/.ssh:Z \
    --rm -it \
    --env-file .env \
    downstream-builder:latest
```

Some notes about this command:

* You MAY remove the `repos` volume mount if you do not want to preserve the cloned repos, but you probably should keep these for sake of performance.
* You MAY remove the `.env` file if you do not want to pass any personalized defaults.
* You MUST include the `ssh-config` volume mount if you intend to build inside Red Hat's network. The base image itself does not include sufficient configs to communicate with the remote servers.

When the container starts, it will ask you several questions with defaults populated by environment variables that may be loaded from your `.env` file. Assuming all goes well, when the requested build tasks complete, the script will dump you back into a `bash` shell (still inside the container) where you may complete any additional steps manually.

The interactive script can create scratch builds, but it currently *does not* create non-scratch *release* builds. If you want to create a release build, you must execute the appropriate commands manually after the interactive script exits. This may change in the future.
