import argparse
import hashlib
import os
import struct

from protocol import FILE_NAME_LENGTH_FIELD_LENGTH
from logger_singleton import SingletonLogger

logger = SingletonLogger.get_logger()


def calculate_md5sum(data):
    hasher = hashlib.md5()
    hasher.update(data)
    return hasher.hexdigest()


def get_directory_path():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", help="Path to the directory to share")
    parsed_args = parser.parse_args()

    assert os.path.exists(parsed_args.directory), f"the path {parsed_args.directory} does not exist"
    assert os.path.isdir(parsed_args.directory), f"the path {parsed_args.directory} is not a directory"
    return parsed_args.directory


async def get_string(reader):
    data = await reader.readexactly(FILE_NAME_LENGTH_FIELD_LENGTH)
    length = struct.unpack(">H", data)[0]

    logger.debug(f"try to read a string of length: {length}")
    received_str = await reader.readexactly(length)
    return received_str


async def get_local_file_path(reader, folder_path: bytes):
    relative_path = await get_string(reader)
    logger.info(f"relative path is {relative_path}")
    logger.info(f"full path is {os.path.join(folder_path, relative_path)}")
    return os.path.join(folder_path, relative_path)


def exception_handler(loop, context):
    # Retrieve the exception object
    exception = context.get('exception')

    if exception:
        logger.exception(exception)
    else:
        print(context["message"])
