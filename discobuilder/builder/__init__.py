from discobuilder.adapter.git import configure_git
from discobuilder.adapter.kerberos import kinit
from discobuilder.builder.server import build_server


def build():
    configure_git()
    kinit()
    # for now, assume we just want to build discovery-server
    build_server()
