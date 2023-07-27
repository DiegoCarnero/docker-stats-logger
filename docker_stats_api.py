import docker
import concurrent.futures
from os import system
from time import sleep

def api_call_loop(container):
    with open(f'./stats/{container}_stats.json', 'w') as stats_file:
        stats = client.api.stats(container=container, decode=None, stream=False)
        stats_file.write(f"{stats['read']};{stats['preread']}")

system('rm ./stats/*.json')
sleep(3)

client = docker.from_env()
containers = client.containers.list()

with concurrent.futures.ThreadPoolExecutor() as executor:
    # Submit the API calls as tasks to the executor
    futures = [executor.submit(api_call_loop, container.name) for container in containers]

# Wait for all tasks to complete and retrieve the results
results = [future.result() for future in concurrent.futures.as_completed(futures)]
