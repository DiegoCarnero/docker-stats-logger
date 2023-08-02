import docker
import concurrent.futures
import json
from os import system
from time import sleep


def api_call_loop(container):
    with open(f'./stats/{container}_stats.log', 'w') as stats_file:
        stats_file.write("datetime;container_name;CPU%;MEM usage;MEM %;NET IN;NET OUT;BLOCK IN;BLOCK OUT\n")
        while True:
            stats = client.api.stats(container=container, decode=None, stream=False, one_shot=False)
            datetime = stats['read'].split(".")[0]
            block_in, block_out = block_io(stats)
            net_in, net_out = network_io(stats)
            stats_file.write(f"{datetime};{container};{calculateCPUPercentUnix(stats)};{stats['memory_stats']['usage']};{calculate_memory_perc(stats)};{net_in};{net_out};{block_in};{block_out}\n")
            # json_formatted_str = json.dumps(stats, indent=2)
            # stats_file.write(json_formatted_str)
            # stats_file.write(f"{stats}\n")
            stats_file.flush()


def calculateCPUPercentUnix(StatsJSON: dict):
    '''
    https://github.com/moby/moby/blob/eb131c5383db8cac633919f82abad86c99bffbe5/cli/command/container/stats_helpers.go#L175
    '''
    cpuPercent = 0.0
    previousCPU = StatsJSON['precpu_stats']['cpu_usage']['total_usage']
    previousSystem = StatsJSON['precpu_stats']['system_cpu_usage']
    # calculate the change for the cpu usage of the container in between readings
    cpuDelta = float(StatsJSON['cpu_stats']['cpu_usage']['total_usage']) - float(previousCPU)
    # calculate the change for the entire system between readings
    systemDelta = float(StatsJSON['cpu_stats']['system_cpu_usage']) - float(previousSystem)

    try:
        online_cpus = len(StatsJSON['cpu_stats']['cpu_usage']['percpu_usage'])
    except KeyError:
        online_cpus = StatsJSON['cpu_stats']['online_cpus']

    if systemDelta > 0.0 and cpuDelta > 0.0:
        cpuPercent = (cpuDelta / systemDelta) * float(online_cpus) * 100.0
    return cpuPercent


def calculate_memory_perc(StatsJSON: dict):
    used_bytes = float(StatsJSON['memory_stats']['usage'])
    limit_bytes = float(StatsJSON['memory_stats']['limit'])

    used_perc = (used_bytes / limit_bytes) * 100.0

    return used_perc


def humanize_bytes(bytesize, precision=2):
    """
    Humanize byte size figures

    https://github.com/TomasTomecek/sen/blob/master/sen/util.py#L60
    https://gist.github.com/moird/3684595
    """
    abbrevs = (
        (1 << 50, 'PB'),
        (1 << 40, 'TB'),
        (1 << 30, 'GB'),
        (1 << 20, 'MB'),
        (1 << 10, 'kB'),
        (1, 'bytes')
    )
    if bytesize == 1:
        return '1 byte'
    for factor, suffix in abbrevs:
        if bytesize >= factor:
            break
    if factor == 1:
        precision = 0
    return '%.*f %s' % (precision, bytesize / float(factor), suffix)


def block_io(StatsJSON: dict):
    io_service_bytes_recursive = StatsJSON['blkio_stats']['io_service_bytes_recursive']
    block_out = 0
    block_in = 0
    for device in io_service_bytes_recursive:
        if device['op'] == 'read':
            block_in += device['value']
        elif device['op'] == 'write':
            block_out += device['value']

    return block_in, block_out


def network_io(StatsJSON: dict):
    networks = StatsJSON['networks']
    net_in = 0
    net_out = 0
    for network, values in networks.items():
        net_in += values['rx_bytes']
        net_out += values['tx_bytes']

    return net_in, net_out


client = docker.from_env()
containers = client.containers.list()

for c in containers:
    api_call_loop(c.name)

with concurrent.futures.ThreadPoolExecutor(max_workers=len(containers)) as executor:
    futures = [executor.submit(api_call_loop, container.name) for container in containers]

# results = [future.result() for future in concurrent.futures.as_completed(futures)]
