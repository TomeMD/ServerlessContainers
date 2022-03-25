# /usr/bin/python
import src.StateDatabase.couchdb as couchDB
import src.StateDatabase.utils as couchdb_utils

cpu_exceeded_upper = dict(
    _id='cpu_exceeded_upper',
    type='rule',
    resource="cpu",
    name='cpu_exceeded_upper',
    rule=dict(
        {"and": [
            {">": [
                {"var": "cpu.structure.cpu.usage"},
                {"var": "cpu.limits.cpu.upper"}]},
            {"<": [
                {"var": "cpu.limits.cpu.upper"},
                {"var": "cpu.structure.cpu.max"}]},
            {"<": [
                {"var": "cpu.structure.cpu.current"},
                {"var": "cpu.structure.cpu.max"}]}
        ]
        }),
    generates="events", action={"events": {"scale": {"up": 1}}},
    active=True
)

cpu_dropped_lower = dict(
    _id='cpu_dropped_lower',
    type='rule',
    resource="cpu",
    name='cpu_dropped_lower',
    rule=dict(
        {"and": [
            {">": [
                {"var": "cpu.structure.cpu.usage"},
                0]},
            {"<": [
                {"var": "cpu.structure.cpu.usage"},
                {"var": "cpu.limits.cpu.lower"}]},
            {">": [
                {"var": "cpu.limits.cpu.lower"},
                {"var": "cpu.structure.cpu.min"}]}]}),
    generates="events",
    action={"events": {"scale": {"down": 1}}},
    active=True
)

# Avoid hysteresis by only rescaling when X underuse events and no bottlenecks are detected, or viceversa
CpuRescaleUp = dict(
    _id='CpuRescaleUp',
    type='rule',
    resource="cpu",
    name='CpuRescaleUp',
    rule=dict(
        {"and": [
            {">=": [
                {"var": "events.scale.up"},
                2]},
            {"<=": [
                {"var": "events.scale.down"},
                2]}
        ]}),
    events_to_remove=2,
    generates="requests",
    action={"requests": ["CpuRescaleUp"]},
    amount=225,
    rescale_by="amount",
    active=True
)

CpuRescaleDown = dict(
    _id='CpuRescaleDown',
    type='rule',
    resource="cpu",
    name='CpuRescaleDown',
    rule=dict(
        {"and": [
            {">=": [
                {"var": "events.scale.down"},
                6]},
            {"==": [
                {"var": "events.scale.up"},
                0]}
        ]}),
    events_to_remove=6,
    generates="requests",
    action={"requests": ["CpuRescaleDown"]},
    amount=-20,
    rescale_by="fit_to_usage",
    active=True,
)
mem_exceeded_upper = dict(
    _id='mem_exceeded_upper',
    type='rule',
    resource="mem",
    name='mem_exceeded_upper',
    rule=dict(
        {"and": [
            {">": [
                {"var": "mem.structure.mem.usage"},
                {"var": "mem.limits.mem.upper"}]},
            {"<": [
                {"var": "mem.limits.mem.upper"},
                {"var": "mem.structure.mem.max"}]},
            {"<": [
                {"var": "mem.structure.mem.current"},
                {"var": "mem.structure.mem.max"}]}

        ]
        }),
    generates="events",
    action={"events": {"scale": {"up": 1}}},
    active=True
)

mem_dropped_lower = dict(
    _id='mem_dropped_lower',
    type='rule',
    resource="mem",
    name='mem_dropped_lower',
    rule=dict(
        {"and": [
            {">": [
                {"var": "mem.structure.mem.usage"},
                0]},
            {"<": [
                {"var": "mem.structure.mem.usage"},
                {"var": "mem.limits.mem.lower"}]},
            {">": [
                {"var": "mem.limits.mem.lower"},
                {"var": "mem.structure.mem.min"}]}]}),
    generates="events",
    action={"events": {"scale": {"down": 1}}},
    active=True
)

MemRescaleUp = dict(
    _id='MemRescaleUp',
    type='rule',
    resource="mem",
    name='MemRescaleUp',
    rule=dict(
        {"and": [
            {">=": [
                {"var": "events.scale.up"},
                2]},
            {"<=": [
                {"var": "events.scale.down"},
                6]}
        ]}),
    generates="requests",
    events_to_remove=2,
    action={"requests": ["MemRescaleUp"]},
    amount=3072,
    rescale_by="amount",
    active=True
)

MemRescaleDown = dict(
    _id='MemRescaleDown',
    type='rule',
    resource="mem",
    name='MemRescaleDown',
    rule=dict(
        {"and": [
            {">=": [
                {"var": "events.scale.down"},
                8]},
            {"==": [
                {"var": "events.scale.up"},
                0]}
        ]}),
    generates="requests",
    events_to_remove=8,
    action={"requests": ["MemRescaleDown"]},
    amount=-512,
    percentage_reduction=50,
    rescale_by="fit_to_usage",
    active=True
)

if __name__ == "__main__":
    initializer_utils = couchdb_utils.CouchDBUtils()
    handler = couchDB.CouchDBServer()
    database = "rules"
    initializer_utils.remove_db(database)
    initializer_utils.create_db(database)
    if handler.database_exists("rules"):
        print("Adding 'rules' documents")
        handler.add_rule(cpu_exceeded_upper)
        handler.add_rule(cpu_dropped_lower)
        handler.add_rule(CpuRescaleUp)
        handler.add_rule(CpuRescaleDown)
        handler.add_rule(mem_exceeded_upper)
        handler.add_rule(mem_dropped_lower)
        handler.add_rule(MemRescaleUp)
        handler.add_rule(MemRescaleDown)
