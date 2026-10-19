#!/usr/bin/env bash
# Ubuntu 24.04 only. Font faces are explicit; no proprietary font download.
set -euo pipefail
source /etc/os-release
test "$ID" = ubuntu && test "$VERSION_ID" = 24.04
privilege=()
if [ "$(id -u)" -ne 0 ]; then privilege=(sudo); fi
"${privilege[@]}" apt-get update
"${privilege[@]}" env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  texlive-xetex=2023.20240207-1 texlive-lang-chinese=2023.20240207-1 \
  texlive-latex-extra=2023.20240207-1 texlive-fonts-recommended=2023.20240207-1 latexmk=1:4.83-1 \
  fonts-noto-cjk=1:20230817+repack1-3 fonts-liberation=1:2.1.5-3 \
  fontconfig poppler-utils
fc-cache -f
mkdir -p _build/pdf-evidence
dpkg-query -W > _build/pdf-evidence/packages.tsv
