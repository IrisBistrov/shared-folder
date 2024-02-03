import os
import json

from logger_singleton import SingletonLogger
from general_utils import calculate_md5sum

logger = SingletonLogger.get_logger()


def calculate_file_md5(file_path):
    with open(file_path, 'rb') as file:
        data = file.read()
    return calculate_md5sum(data)


def directory_to_json(dir_path):
    dir_dict = {}
    for root, dirs, files in os.walk(dir_path):
        for file_path in files:
            full_path = os.path.join(root, file_path)
            # all the paths in the dictionary are relative to the shared library
            relative_path = os.path.relpath(full_path, dir_path)
            md5sum = calculate_file_md5(full_path)
            dir_dict[relative_path] = md5sum

    logger.info(f"the dir dict is: {dir_dict}")
    return json.dumps(dir_dict, indent=4)
