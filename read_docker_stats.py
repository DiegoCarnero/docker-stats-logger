# https://naartti.medium.com/analyse-docker-stats-with-python-pandas-2c2ed735cfcd

import subprocess
from datetime import datetime

header = ["CONTAINER ID","NAME","CPU %","MEM USAGE / LIMIT","MEM %","NET I/O","BLOCK I/O","PIDS"]

with open("docker_stats.txt", "w") as outfile:
  while True:
    try:
      subprocess.call('docker stats --no-stream', shell=True, stdout=outfile)
      date = datetime.now()
      date = date.replace(microsecond=0)
      outfile.write(f"timestamp   {date}\n")
      outfile.flush()
    except KeyboardInterrupt:
      break

with open("docker_stats.txt", "r") as file:
  file.readline()
  entry = file.readline().split("   ")

entry = list(filter(('').__ne__, entry))
for ndx, field in enumerate(entry):
  entry[ndx] = field.strip()
print(entry)