import asyncio
import json
import os
import struct

from pathlib import Path

from logger_singleton import SingletonLogger
from protocol import MESSAGE_TYPE_LENGTH, MESSAGE_LENGTH_FIELD_LENGTH, MessageType, UserRequestMessage
from directory_utils import calculate_md5
from general_utils import get_directory_path, get_string, get_local_file_path, exception_handler
from folder_monitor import async_main

logger = SingletonLogger.get_logger()

shared_dir_path = ""


async def handle_missing_file(missing_file_path, missing_hash, reader, writer):
    writer.write(UserRequestMessage(missing_file_path, missing_hash).pack())
    await writer.drain()
    data = await reader.readexactly(MESSAGE_TYPE_LENGTH)
    message_type = struct.unpack(">B", data)[0]
    assert message_type is MessageType.SERVER_FILE.value

    file_path = await get_local_file_path(reader, shared_dir_path.encode())
    content = await get_string(reader)
    md5sum = await reader.readexactly(32)

    assert md5sum == missing_hash.encode()
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(os.path.join(shared_dir_path, missing_file_path), "wb") as f:
        f.write(content)


async def handle_modified_file(actual_file_path, expected_md5, reader, writer):
    os.unlink(actual_file_path)
    await handle_missing_file(actual_file_path, expected_md5, reader, writer)


async def verify_directory_contents(directory_dict, dir_path, reader, writer):
    for file_path, expected_md5 in directory_dict.items():
        actual_file_path = os.path.join(dir_path, file_path)

        if not os.path.exists(actual_file_path):
            logger.info(f"file missing: {actual_file_path}")
            relative_path = os.path.relpath(actual_file_path, shared_dir_path)
            await handle_missing_file(relative_path, expected_md5, reader, writer)
            continue

        actual_md5 = calculate_md5(actual_file_path)
        if actual_md5 != expected_md5:
            logger.info(f"MD5 mismatch for {actual_file_path}: Expected {expected_md5}, got {actual_md5}")
            await handle_modified_file(actual_file_path, expected_md5, reader, writer)
        else:
            logger.info(f"file verified: {actual_file_path}")

    paths = [Path(file_path) for file_path in directory_dict.keys()]
    for root, dirs, files in os.walk(dir_path):
        for curr_file in files:
            full_path = os.path.join(root, curr_file)
            relative_path = os.path.relpath(full_path, dir_path)
            same_paths = [path for path in paths if path == Path(relative_path)]
            if len(same_paths) == 0:
                logger.info(f"File exists locally but not in remote: {relative_path}")
                os.unlink(full_path)


async def handle_sync(reader, writer):
    logger.info("handle server sync message")
    data = await reader.readexactly(MESSAGE_LENGTH_FIELD_LENGTH)
    data = await reader.readexactly(struct.unpack(">H", data)[0])
    dir_dict = json.loads(data.decode())
    logger.info(f"received the dir dict: {dir_dict}")
    await verify_directory_contents(dir_dict, shared_dir_path, reader, writer)


async def shared_folder_client(host, port):
    reader, writer = await asyncio.open_connection(host, port)

    while True:
        data = await reader.readexactly(MESSAGE_TYPE_LENGTH)
        message_type = struct.unpack(">B", data)[0]
        logger.info(f'Received message of type: {message_type}')

        if message_type != MessageType.SERVER_SYNC.value:
            logger.error(f"unrecognizable message code {message_type}")
            break

        await handle_sync(reader, writer)

    logger.info('Close the connection')
    writer.close()
    await writer.wait_closed()


async def main():
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(exception_handler)

    global shared_dir_path
    shared_dir_path = get_directory_path()
    logger.info(f"The path that we will sync with the shared folder is {shared_dir_path}")

    await asyncio.gather(shared_folder_client('localhost', 8080), async_main())


asyncio.run(main(), debug=True)
