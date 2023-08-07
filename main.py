import argparse
import os
from logger.logger import run

parser = argparse.ArgumentParser(description="Log Docker's system utilization.",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-c", "--config_file", help="Path to config file.")  # TODO actually implement this
parser.add_argument("-d", "--directory", help='Directory where log files will be stored.', default=os.getcwd()+"/stats")
parser.add_argument("-m", "--mode", help='Archive mode. Options: summary, raw, full', default="full")
parser.add_argument("-p", "--project_name", help="Project name. Only containers whose name begins with the provided project name will be monitored. Otherwise, all containers will be monitored.", default="")


if __name__ == "__main__":
    config = vars(parser.parse_args())
    run(config)
