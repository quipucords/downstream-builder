import sys

from discobuilder.builder import build

if __name__ == "__main__":
    if not sys.__stdin__.isatty():
        raise Exception("This script requires an interactive terminal.")
    build()
