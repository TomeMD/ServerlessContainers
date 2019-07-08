# /usr/bin/python
from __future__ import print_function

from threading import Thread
import requests
import json
import time
import traceback
import logging

import src.StateDatabase.couchdb as couchDB
import src.MyUtils.MyUtils as MyUtils

db_handler = couchDB.CouchDBServer()
rescaler_http_session = requests.Session()
RESOURCES = ["cpu", "mem"]
translate_map = {
    "cpu": {"metric": "structure.cpu.current", "limit_label": "effective_cpu_limit"},
    "mem": {"metric": "structure.mem.current", "limit_label": "mem_limit"},
    "disk": {"metric": "structure.disk.current", "limit_label": "disk_read_limit"},  # FIXME missing write value
    "net": {"metric": "structure.net.current", "limit_label": "net_limit"}
}
SERVICE_NAME = "structures_snapshoter"
CONFIG_DEFAULT_VALUES = {"POLLING_FREQUENCY": 10, "DEBUG": True, "PERSIST_APPS": True}
MAX_FAIL_NUM = 5
debug = True


def generate_timeseries(container_name, resources):
    timestamp = int(time.time())

    for resource in RESOURCES:
        value = resources[resource][translate_map[resource]["limit_label"]]
        metric = translate_map[resource]["metric"]
        timeseries = dict(metric=metric, value=value, timestamp=timestamp, tags=dict(host=container_name))

        print(json.dumps(timeseries))


def update_container_current_values(container_name, resources):
    if not resources:
        MyUtils.log_error("Unable to get resource info for container {0}".format(container_name), debug)

    # Remote database operation
    database_structure = db_handler.get_structure(container_name)
    new_structure = MyUtils.copy_structure_base(database_structure)
    new_structure["resources"] = dict()
    for resource in RESOURCES:
        if resource not in new_structure:
            new_structure["resources"][resource] = dict()

        if resource not in resources or not resources[resource]:
            MyUtils.log_error("Unable to get info for resource {0} for container {1}".format(resource, container_name),
                              debug)
            new_structure["resources"][resource]["current"] = 0
        else:
            new_structure["resources"][resource]["current"] = resources[resource][
                translate_map[resource]["limit_label"]]

    # Remote database operation
    MyUtils.update_structure(new_structure, db_handler, debug, max_tries=3)


def thread_persist_container(container):
    container_name = container["name"]

    # Try to get the container resources, if unavailable, continue with others
    # Remote operation
    resources = MyUtils.get_container_resources(container, rescaler_http_session, debug)
    if not resources:
        MyUtils.log_error("Couldn't get container's {0} resources".format(container_name), debug)
        return

    # Persist by updating the Database current value
    update_container_current_values(container_name, resources)

    # Persist through time series sent to OpenTSDB
    # generate_timeseries(container_name, resources)


def persist_containers():
    # Try to get the containers, if unavailable, return
    # Remote database operation
    containers = MyUtils.get_structures(db_handler, debug, subtype="container")
    if not containers:
        return

    # Retrieve each container resources, persist them and store them to generate host info
    container_resources_dict = dict()

    # UNTHREADED, allows cacheable container information
    # for container in containers:
    #    thread_persist_container(container, container_resources_dict)
    # return container_resources_dict

    # THREADED, doesn't allow cacheable container information
    threads = []
    for container in containers:
        process = Thread(target=thread_persist_container, args=(container,))
        process.start()
        threads.append(process)

    for process in threads:
        process.join()


def persist_applications(container_resources_dict):
    # Try to get the applications, if unavailable, return
    # Remote database operation
    applications = MyUtils.get_structures(db_handler, debug, subtype="application")
    if not applications:
        return

    # Generate the applications current resource values
    for app in applications:
        for resource in RESOURCES:
            app["resources"][resource]["current"] = 0

        application_containers = app["containers"]
        for container_name in application_containers:

            if container_name not in container_resources_dict:
                MyUtils.log_error(
                    "Container info {0} is missing for app : {1}".format(container_name, app["name"])
                    + " app info will not be totally accurate", debug)
                continue

            for resource in RESOURCES:
                try:
                    current_resource_label = translate_map[resource]["limit_label"]
                    container_resources = container_resources_dict[container_name]["resources"]

                    if resource not in container_resources or not container_resources[resource]:
                        MyUtils.log_error(
                            "Unable to get info for resource {0} for container {1} when computing {2} resources".format(
                                resource, container_name, app["name"]), debug)
                    else:
                        app["resources"][resource]["current"] += container_resources[resource][current_resource_label]
                except KeyError:
                    if "name" in container_resources_dict[container_name] and "name" in app:
                        MyUtils.log_error(
                            "Container info {0} is missing for app : {1} and resource {2} resource,".format(
                                container_name, app["name"], resource)
                            + " app info will not be totally accurate", debug)
                    else:
                        MyUtils.log_error("Error with app or container info", debug)
                        # TODO this error should be more self-explanatory

        # Remote database operation
        MyUtils.update_structure(app, db_handler, debug)


def get_container_resources_dict():
    # Remote database operation
    containers = MyUtils.get_structures(db_handler, debug, subtype="container")
    container_list_names = [c["name"] for c in containers]
    if not containers:
        return

    # Get all the different hosts of the containers
    diff_hosts = dict()
    for container in containers:
        container_host = container["host"]
        if container_host not in diff_hosts:
            diff_hosts[container_host] = dict()
            diff_hosts[container_host]["host_rescaler_ip"] = container["host_rescaler_ip"]
            diff_hosts[container_host]["host_rescaler_port"] = container["host_rescaler_port"]

    # For each host, retrieve its containers and persist the ones we look for
    container_resources_dict = dict()
    for hostname in diff_hosts:
        host = diff_hosts[hostname]
        host_containers = MyUtils.get_host_containers(host["host_rescaler_ip"], host["host_rescaler_port"],
                                                      rescaler_http_session, debug)
        for container_name in host_containers:
            if container_name in container_list_names:
                container_resources_dict[container_name] = host_containers[container_name]

    container_resources_dictV2 = dict()
    for container in containers:
        container_name = container["name"]
        container_resources_dictV2[container_name] = container
        container_resources_dictV2[container_name]["resources"] = container_resources_dict[container_name]

    # Retrieve each container resources, persist them and store them to generate host info
    # container_resources_dict = dict()

    # for container in containers:
    #     container_name = container["name"]
    #
    #     # Remote operation
    #     resources = MyUtils.get_container_resources(container, rescaler_http_session, debug)
    #     if not resources:
    #         MyUtils.log_error("Couldn't get container's {0} resources".format(container_name), debug)
    #         continue
    #
    #     container_resources_dict[container_name] = container
    #     container_resources_dict[container_name]["resources"] = resources
    return container_resources_dictV2


def persist_thread():
    # Process and measure time
    epoch_start = time.time()

    # UNTHREDAED for cacheable container information
    # container_resources_dict = persist_containers()
    # persist_applications(container_resources_dict)

    # FULLY THREADED, more requests but faster due to parallelism

    ###
    persist_containers()
    # if persist_applications_structures:
    #    container_resources_dict = get_container_resources_dict()
    #    persist_applications(container_resources_dict)
    ###
    container_resources_dict = get_container_resources_dict()
    persist_applications(container_resources_dict)

    epoch_end = time.time()
    processing_time = epoch_end - epoch_start
    MyUtils.log_info("It took {0} seconds to snapshot structures".format(str("%.2f" % processing_time)), debug)


def persist():
    logging.basicConfig(filename=SERVICE_NAME + '.log', level=logging.INFO)

    global debug
    global persist_applications_structures
    while True:
        # Get service info
        # Remote database operation
        service = MyUtils.get_service(db_handler, SERVICE_NAME)

        # Heartbeat
        # Remote database operation
        MyUtils.beat(db_handler, SERVICE_NAME)

        # CONFIG
        config = service["config"]
        polling_frequency = MyUtils.get_config_value(config, CONFIG_DEFAULT_VALUES, "POLLING_FREQUENCY")
        debug = MyUtils.get_config_value(config, CONFIG_DEFAULT_VALUES, "DEBUG")
        persist_applications_structures = MyUtils.get_config_value(config, CONFIG_DEFAULT_VALUES, "PERSIST_APPS")

        thread = Thread(target=persist_thread, args=())
        thread.start()
        MyUtils.log_info("Structures snapshoted at {0}".format(MyUtils.get_time_now_string()), debug)
        time.sleep(polling_frequency)

        if thread.isAlive():
            delay_start = time.time()
            MyUtils.log_warning(
                "Previous thread didn't finish before next poll is due, with polling time of {0} seconds, at {1}".format(
                    str(polling_frequency), MyUtils.get_time_now_string()), debug)
            MyUtils.log_warning("Going to wait until thread finishes before proceeding", debug)
            thread.join()
            delay_end = time.time()
            MyUtils.log_warning("Resulting delay of: {0} seconds".format(str(delay_end - delay_start)), debug)


def main():
    try:
        persist()
    except Exception as e:
        MyUtils.log_error("{0} {1}".format(str(e), str(traceback.format_exc())), debug=True)


if __name__ == "__main__":
    main()