#!/usr/bin/env bash
export ORCHESTRATOR_PATH=$HOME/development/AutomaticRescaler/src/Orchestrator/

nodes=( node0 node1 node2 node3 node4 node5 )
guarded_resources=( cpu mem )
unguarded_resources=( disk net energy )
resource_rules=( CpuRescaleDown CpuRescaleUp MemRescaleDown MemRescaleUp cpu_dropped_lower cpu_exceeded_upper mem_dropped_lower mem_exceeded_upper )
energy_rules=( EnergyRescaleDown EnergyRescaleUp energy_dropped_lower energy_exceeded_upper )

echo "Setting Guardian to guard containers"
bash $ORCHESTRATOR_PATH/Guardian/set_to_fixed.sh > /dev/null

echo "Setting application to unguarded"
bash $ORCHESTRATOR_PATH/Structures/set_to_unguarded.sh app1 > /dev/null

echo "Setting container nodes to guarded"
for i in "${nodes[@]}"
do
	bash $ORCHESTRATOR_PATH/Structures/set_to_guarded.sh $i > /dev/null
done

echo "Setting container to fixed"
for i in "${nodes[@]}"
do
	bash $ORCHESTRATOR_PATH/Structures/set_policy_to_fixed.sh $i > /dev/null
done
echo "Setting container resources [cpu,mem] to guarded"
for i in "${nodes[@]}"
do
    bash $ORCHESTRATOR_PATH/Structures/set_many_resource_to_guarded.sh $i ${guarded_resources[@]} > /dev/null
done

echo "Setting container resources [disk,net,energy] to unguarded"
for i in "${nodes[@]}"
do
    bash $ORCHESTRATOR_PATH/Structures/set_many_resource_to_unguarded.sh $i ${unguarded_resources[@]} > /dev/null
done

#echo "Setting container resources [cpu] to normal"
#for i in "${nodes[@]}"
#do
#    bash $RESCALER_PATH/Orchestrator/Structures/set_structure_cpu_max.sh $i 200 > /dev/null
#done

echo "Activating resource rules"
for i in "${resource_rules[@]}"
do
    bash $ORCHESTRATOR_PATH/Rules/activate_rule.sh $i > /dev/null
done

echo "Deactivating energy rules"
for i in "${energy_rules[@]}"
do
    bash $ORCHESTRATOR_PATH/Rules/deactivate_rule.sh $i > /dev/null
done
