#!/usr/bin/env bash
scriptDir=$(dirname -- "$(readlink -f -- "$BASH_SOURCE")")
source "${scriptDir}/../../set_pythonpath.sh"
tmux new -d -s "Orchestrator" "python3 src/Orchestrator/Orchestrator.py 2> orchestrator.log"
