import docker
import concurrent.futures
import csv
import logger.utils as utils
from os import makedirs
from time import sleep


directory = ""
project = ""
interval = 0
one_shot = False


def log_summary(container, client):
    with open(f'{directory}/{container}_stats.csv', 'w') as stats_file:
        stats_file.write("datetime;container_name;CPU%;MEM usage;MEM %;NET IN;NET OUT;BLOCK IN;BLOCK OUT\n")
        while True:
            stats = api_call(client, container)
            datetime = stats['read'].split(".")[0]
            block_in, block_out = utils.block_io(stats)
            net_in, net_out = utils.network_io(stats)
            stats_file.write(f"{datetime};{container};{utils.calculateCPUPercentUnix(stats)};{stats['memory_stats']['usage']};{utils.calculate_memory_perc(stats)};{net_in};{net_out};{block_in};{block_out}\n")
            stats_file.flush()


def log_raw(container, client):
    with open(f'{directory}/{container}_stats.log', 'w') as stats_file:
        while True:
            stats = api_call(container=container)
            stats_file.write(f"{stats}\n")
            stats_file.flush()


def log_full_as_csv(container, client):
    # TODO simplify column names after flattening
    sep = ";"
    with open(f'{directory}/{container}_stats.csv', 'w') as stats_file:
        header_written = False
        while True:
            stats = api_call(client, container)
            flattened_stats = utils.flatten(stats)
            if not header_written:
                csv_columns = flattened_stats.keys()
                writer = csv.DictWriter(stats_file, fieldnames=csv_columns, delimiter=sep, extrasaction='ignore')
                writer.writeheader()
                header_written = True
            writer.writerow(flattened_stats)
            stats_file.flush()


def api_call(client, container_name_or_id):
    global interval
    global one_shot
    sleep_interval = max(0, interval - 1)  # -1 to account for the API's minimum delay. Calculating running average would be ideal
    sleep(sleep_interval)
    return client.api.stats(container=container_name_or_id, decode=None, stream=False, one_shot=one_shot)


def run(config: dict):
    client = docker.from_env()
    containers_all = client.containers.list()
    container_names = list()
    global directory
    global interval
    global one_shot
    global project
    log_modes = {"summary": log_summary, "full": log_full_as_csv, "raw": log_raw}

    if config.get("config_file") is None:
        project = config.get("project_name", "")
        directory = config.get("directory")
        mode = config.get("mode")
        interval = config.get("interval")
        one_shot = config.get("one-shot")

    if mode == 'summary':
        one_shot = False

    if project != "":
        directory = f'{directory}/{project}'
    makedirs(directory, exist_ok=True)

    [container_names.append(c.name) for c in containers_all if c.name.startswith(project)]

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(container_names)) as executor:
        futures = [executor.submit(log_modes.get(mode), container, client) for container in container_names]
    print("Logging...")
