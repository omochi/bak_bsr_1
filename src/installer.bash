#!/bin/bash
set -ueo pipefail
cd "/usr/local/lib"
git clone "https://github.com/omochi/bsr.git"
cd "bsr"
"src/install.bash"
