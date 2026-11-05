#!/bin/sh
# 저장소 로컬 git 훅 활성화 (core.hooksPath -> .githooks)
set -eu
cd "$(dirname "$0")/.."
git config core.hooksPath .githooks
echo "core.hooksPath = $(git config core.hooksPath)"
echo "활성 훅: $(ls .githooks)"
echo "해제: git config --unset core.hooksPath"
