import os
import json

from shared_folder_opu.logger_singleton import SingletonLogger
from shared_folder_opu.general_utils import calculate_md5sum

logger = SingletonLogger.get_logger()


def calculate_file_md5(file_path: str):
    """
    calculate md5sum of the file path
    """
    with open(file_path, 'rb') as file:
        data = file.read()
    return calculate_md5sum(data)


def directory_to_json(dir_path: str):
    """
    create a json object of the shared folder. one dict is created for the dirs and one for the files.
    """
    file_to_hash = {}
    directories = []
    for root, dirs, files in os.walk(dir_path):
        for directory in dirs:
            full_path = os.path.join(root, directory)
            relative_path = os.path.relpath(full_path, dir_path)
            directories.append(relative_path)

        for file_path in files:
            full_path = os.path.join(root, file_path)
            relative_path = os.path.relpath(full_path, dir_path)
            md5sum = calculate_file_md5(full_path)
            file_to_hash[relative_path] = md5sum

    logger.debug(f"the files and their hashes: {file_to_hash}")
    logger.debug(f"the directories are: {directories}")
    directory_structure = (file_to_hash, directories)
    return json.dumps(directory_structure, indent=4)
