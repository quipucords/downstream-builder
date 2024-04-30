FROM fedora:40

RUN dnf install -y \
    krb5-workstation git man vim which chkconfig java-headless cargo packit \
    python3-pip python3-devel python3-setuptools \
    python3-poetry python3-rich python3-pyyaml \
    && curl -k -L -o /tmp/redhat-internal-cert-install-0.1-31.el7.noarch.rpm \
    https://hdn.corp.redhat.com/rhel7-csb-stage/RPMS/noarch/redhat-internal-cert-install-0.1-31.el7.noarch.rpm \
    && rpm -ivh /tmp/redhat-internal-cert-install-0.1-31.el7.noarch.rpm \
    && rm -f /tmp/redhat-internal-cert-install-0.1-31.el7.noarch.rpm \
    && curl -L -o /etc/yum.repos.d/rcm-tools-fedora.repo https://download.devel.redhat.com/rel-eng/RCMTOOLS/rcm-tools-fedora.repo \
    && dnf install -y rhpkg brewkoji \
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
