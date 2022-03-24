#!/usr/bin/env bash
scriptDir=$(dirname -- "$(readlink -f -- "$BASH_SOURCE")")
source "${scriptDir}/../set_env.sh"

if [ -z "$3" ]
then
      echo "3 arguments are needed"
      exit 1
fi
curl -X PUT -H "Content-Type: application/json" http://${ORCHESTRATOR_REST_URL}/structure/$1/limits/$2/boundary  -d '{"value":"'$3'"}'
