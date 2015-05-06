#!/bin/bash
set -ueo pipefail
src_dir=$(cd "$(dirname "$0")"; pwd)
cd "/usr/local/bin"
ln -sfh "$src_dir/bsr" "bsr"
