import os
import hashlib
import json

from logger_singleton import SingletonLogger

logger = SingletonLogger.get_logger()


def calculate_md5(file_path):
    hasher = hashlib.md5()
    with open(file_path, 'rb') as file:
        buf = file.read()
        hasher.update(buf)
    return hasher.hexdigest()


def directory_to_json(dir_path):
    dir_dict = {}
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            file_path = os.path.join(root, file)
            md5sum = calculate_md5(file_path)
            dir_dict[file_path] = md5sum
    return json.dumps(dir_dict, indent=4)
