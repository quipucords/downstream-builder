```sh
# create local dir for sharing repos and virtualenv cache
mkdir repos

# edit .env as needed
cp .env-example .env

docker build -t discovery-downstream-builder:latest .

docker run \
    -v "$PWD"/repos:/repos
    --rm -it \
    --env-file .env \
    discovery-downstream-builder:latest
````
