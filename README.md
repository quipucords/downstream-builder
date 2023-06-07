# Discovery Downstream Builder

## What is this?

This is a helper container+script to simplify the quipucords-to-Discovery downstream build process. This means you don't need to install `rhpkg` and `brewkoji` on your own machine or run a custom VM with them any longer!

## How do I use it?

Optionally create local dir for sharing repos and virtualenv cache:

```sh
mkdir repos
```

Edit a `.env` file as needed:

```sh
cp .env-example .env
vi .env
```

Build it locally if you wish:

```sh
docker build -t discovery-downstream-builder:latest .
```

Run it! Remove the `-v` if you don't want the shared dir.

```sh
docker run \
    -v "$PWD"/repos:/repos \
    --rm -it \
    --env-file .env \
    discovery-downstream-builder:latest
````

When the container starts, it will ask you several questions with defaults populated by environment variables that may be loaded from your `.env` file. Assuming all goes well, eventually my automation ends, and it will dump you back into a `bash` shell (still inside the container) where you must complete the remaining steps manually.
