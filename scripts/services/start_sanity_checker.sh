#!/usr/bin/env bash
scriptDir=$(dirname -- "$(readlink -f -- "$BASH_SOURCE")")
source "${scriptDir}/../../set_pythonpath.sh"
tmux new -d -s "SanityChecker" "python3 src/SanityChecker/SanityChecker.py"
