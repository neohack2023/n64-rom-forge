FROM --platform=linux/amd64 ubuntu@sha256:79676deb51ebb02885b0b9d33788e78a37cf1045ad79d1bb04c6a222c3556b3d

ARG DEBIAN_FRONTEND=noninteractive
ARG SNAPSHOT=20260810T000000Z

COPY scripts/resolve_ubuntu_snapshot.py /usr/local/bin/resolve_ubuntu_snapshot.py

RUN set -eux; \
    printf '%s\n' \
      "deb [check-valid-until=no] http://snapshot.ubuntu.com/ubuntu/${SNAPSHOT} jammy main universe" \
      "deb [check-valid-until=no] http://snapshot.ubuntu.com/ubuntu/${SNAPSHOT} jammy-updates main universe" \
      "deb [check-valid-until=no] http://snapshot.ubuntu.com/ubuntu/${SNAPSHOT} jammy-security main universe" \
      > /etc/apt/sources.list; \
    rm -rf /etc/apt/sources.list.d/*; \
    apt-get -o Acquire::Check-Valid-Until=false update; \
    mkdir -p /n64rf/evidence /var/cache/apt/archives; \
    apt-get -o Acquire::Check-Valid-Until=false -y --download-only install \
      binutils-mips-linux-gnu bsdextrautils build-essential gcc-mips-linux-gnu libcapstone-dev pkgconf python3; \
    : > /n64rf/evidence/transaction-packages.tsv; \
    for f in /var/cache/apt/archives/*.deb; do \
      [ -e "$f" ] || continue; \
      p="$(dpkg-deb -f "$f" Package)"; v="$(dpkg-deb -f "$f" Version)"; a="$(dpkg-deb -f "$f" Architecture)"; \
      s="$(sha256sum "$f" | awk '{print $1}')"; \
      printf '%s\t%s\t%s\t%s\t%s\n' "$p" "$v" "$a" "$(basename "$f")" "$s" >> /n64rf/evidence/transaction-packages.tsv; \
    done; \
    sort -o /n64rf/evidence/transaction-packages.tsv /n64rf/evidence/transaction-packages.tsv; \
    apt-get -o Acquire::Check-Valid-Until=false -y install \
      binutils-mips-linux-gnu bsdextrautils build-essential gcc-mips-linux-gnu libcapstone-dev pkgconf python3; \
    python3 /usr/local/bin/resolve_ubuntu_snapshot.py \
      --lane hackersm64 --snapshot "${SNAPSHOT}" \
      --transaction /n64rf/evidence/transaction-packages.tsv \
      --output /n64rf/evidence/lane.json \
      --executables mips-linux-gnu-as mips-linux-gnu-ld mips-linux-gnu-objdump mips-linux-gnu-objcopy mips-linux-gnu-gcc make python3 pkgconf \
      --direct-packages binutils-mips-linux-gnu bsdextrautils build-essential gcc-mips-linux-gnu libcapstone-dev pkgconf python3
