FROM quay.io/rhel-devel-tools/rhel-developer-toolbox:latest

RUN dnf install -y \
    python3.11-devel python3.11-setuptools python3.11-jinja2 python3-sphinx \
    python3.11-poetry python3.11-rich python3.11-pyyaml \
    krb5-workstation git man vim which chkconfig java-headless cargo \
    && dnf clean all

RUN rpmdev-setuptree

COPY configs/krb5.conf /etc/krb5.conf
COPY configs/gitconfig /root/.gitconfig
COPY scripts/helper.sh /helper.sh
COPY scripts/helper.py /helper.py
RUN chmod 755 /helper.py /helper.sh

ENTRYPOINT /helper.sh
