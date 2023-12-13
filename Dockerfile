FROM fedora:38

RUN dnf install -y \
    krb5-workstation git man vim which chkconfig java-headless cargo packit \
    python3.11-pip python3.11-devel python3.11-setuptools \
    python3.11-poetry python3.11-rich python3.11-pyyaml \
    && curl -k -L -o /tmp/redhat-internal-cert-install-0.1-31.el7.noarch.rpm \
    https://hdn.corp.redhat.com/rhel7-csb-stage/RPMS/noarch/redhat-internal-cert-install-0.1-31.el7.noarch.rpm \
    && rpm -ivh /tmp/redhat-internal-cert-install-0.1-31.el7.noarch.rpm \
    && rm -f /tmp/redhat-internal-cert-install-0.1-31.el7.noarch.rpm \
    && curl -L -o /etc/yum.repos.d/rcm-tools-fedora.repo https://download.devel.redhat.com/rel-eng/RCMTOOLS/rcm-tools-fedora.repo \
    && dnf install -y rhpkg brewkoji \
    && rm -f /etc/yum.repos.d/rcm-tools-fedora.repo \
    && dnf clean all

RUN rpmdev-setuptree

COPY configs/krb5.conf /etc/krb5.conf
COPY configs/gitconfig /root/.gitconfig
COPY scripts/helper.sh /helper.sh
COPY discobuilder /discobuilder
RUN chmod 755 /helper.sh

ENTRYPOINT /helper.sh
