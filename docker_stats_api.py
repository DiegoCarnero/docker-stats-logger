import docker
import concurrent.futures
from os import system
from time import sleep

def api_call_loop(container):
    with open(f'./stats/{container}_stats.log', 'w') as stats_file:
        for n in range(2):
            stats = client.api.stats(container=container, decode=None, stream=False, one_shot=False)
            # stats_file.write(f"{stats}")
            stats_file.write(f"{stats['read']};{container};{calculateCPUPercentUnix(stats)};{humanize_bytes(stats['memory_stats']['usage'])};{calculate_memory_perc(stats)}\n")

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

    if systemDelta > 0.0 and cpuDelta > 0.0:
        cpuPercent = (cpuDelta / systemDelta) * float(len(StatsJSON['cpu_stats']['cpu_usage']['percpu_usage'])) * 100.0
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


client = docker.from_env()
containers = client.containers.list()

with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [executor.submit(api_call_loop, container.name) for container in containers]

# results = [future.result() for future in concurrent.futures.as_completed(futures)]
