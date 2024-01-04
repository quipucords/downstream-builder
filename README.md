# Quipucords Downstream Builder

## What is this?

This is a containerized interactive script to simplify the quipucords-to-Discovery downstream build process. This means you don't need to install `rhpkg` and `brewkoji` on your own machine or run a custom VM with them any longer!

This script can trigger container builds for quipucords (Discovery) or RPMs for qpc (discovery-cli).

## How do I use it?

Optionally create a local directory for sharing repos and virtualenv cache (this can speed up subsequent runs and allows you to access the files from your host):

```sh
mkdir repos
```

Optionally edit a `.env` file as needed:

```sh
cp .env-example .env
vi .env
```

Build the container image:

```sh
podman build -t downstream-builder:latest .
```

Connect to the Red Hat VPN. This program communicates with several internal hosts and will fail without appropriate network access.

Run it! Remove the `-v` or `--env-file` arguments if you do not wish to use the shared directory or env file.

```sh
podman run \
    -v "$PWD"/repos:/repos \
    --rm -it \
    --env-file .env \
    downstream-builder:latest
````

When the container starts, it will ask you several questions with defaults populated by environment variables that may be loaded from your `.env` file. Assuming all goes well, when the requested build tasks complete, the script will dump you back into a `bash` shell (still inside the container) where you may complete any additional steps manually.

The interactive script can create scratch builds, but it currently *does not* create non-scratch *release* builds. If you want to create a release build, you must execute the appropriate commands manually after the interactive script exits. This may change in the future.
