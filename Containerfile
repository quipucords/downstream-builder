FROM fedora:40

RUN dnf install -y \
    krb5-workstation git man vim which chkconfig java-headless cargo packit \
    python3-pip python3-devel python3-setuptools \
    python3-rich python3-pyyaml \
    && curl -L -o /etc/pki/ca-trust/source/anchors/Current-IT-Root-CAs.pem https://certs.corp.redhat.com/certs/Current-IT-Root-CAs.pem \
    && update-ca-trust \
    && curl -L -o /etc/yum.repos.d/rcm-tools-fedora.repo https://download.devel.redhat.com/rel-eng/RCMTOOLS/rcm-tools-fedora.repo \
    && dnf install -y rhpkg brewkoji \
    && cp /etc/pki/ca-trust/source/anchors/Current-IT-Root-CAs.pem /etc/pki/brew/RH-IT-Root-CA.crt \
    && rm -f /etc/yum.repos.d/rcm-tools-fedora.repo \
    && dnf clean all

COPY configs/krb5.conf /etc/krb5.conf
COPY scripts/helper.sh /helper.sh
COPY discobuilder /discobuilder
RUN chmod 555 /helper.sh
RUN mkdir -p /repos
RUN useradd -ms /bin/bash builder
RUN chown builder /repos

USER builder
COPY configs/gitconfig /home/builder/.gitconfig
RUN rpmdev-setuptree

ENTRYPOINT /helper.sh
