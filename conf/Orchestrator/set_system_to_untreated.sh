#!/usr/bin/env bash

export SERVERLESS_PATH=$HOME/ServerlessContainers
export ORCHESTRATOR_PATH=${SERVERLESS_PATH}/scripts/orchestrator

nodes=( node0 node1 node2 node3 node4 node5 node6 node7 )
resources=( cpu )

echo "Setting Guardian to guard containers"
bash $ORCHESTRATOR_PATH/Guardian/set_to_container.sh > /dev/null

echo "Setting container resources to unguarded"
for i in "${nodes[@]}"
do
    bash $ORCHESTRATOR_PATH/Structures/set_many_resource_to_unguarded.sh $i ${resources[@]} > /dev/null
done

echo "Setting container nodes to unguarded"
for i in "${nodes[@]}"
do
	bash $ORCHESTRATOR_PATH/Structures/set_to_unguarded.sh $i > /dev/null
done
