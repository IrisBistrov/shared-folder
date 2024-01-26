import asyncio
import json
import os
import struct

from pathlib import Path

from logger_singleton import SingletonLogger
from protocol import MESSAGE_TYPE_LENGTH, MESSAGE_LENGTH_FIELD_LENGTH, MessageType, UserRequestMessage
from directory_utils import calculate_md5

logger = SingletonLogger.get_logger()


async def handle_missing_file(missing_file_path, missing_hash, reader, writer):
    writer.write(UserRequestMessage(missing_file_path, missing_hash).pack())
    message_type = await reader.read(MESSAGE_TYPE_LENGTH)
    assert message_type is MessageType.SERVER_FILE.value

    file_path_length = struct.unpack(">H", reader.read(2))
    content_length = struct.unpack(">H", reader.read(2))
    md5sum = await reader.read(16)
    file_path = await reader.read(file_path_length)
    content = await reader.read(content_length)

    assert file_path == missing_file_path
    logger.info(f"received the content of the file {missing_file_path} with the hash {md5sum}")

    with open(missing_file_path) as f:
        f.write(content)


async def handle_modified_file(actual_file_path, expected_md5, reader, writer):
    Path(actual_file_path).unlink()
    await handle_missing_file(actual_file_path, expected_md5, reader, writer)


async def verify_directory_contents(directory_dict, dir_path, reader, writer):
    for file_path, expected_md5 in directory_dict.items():
        actual_file_path = os.path.join(dir_path, file_path)

        if not os.path.exists(actual_file_path):
            logger.info(f"File missing: {actual_file_path}")
            await handle_missing_file(actual_file_path, expected_md5, reader, writer)
            continue

        actual_md5 = calculate_md5(actual_file_path)
        if actual_md5 != expected_md5:
            logger.info(f"MD5 mismatch for {actual_file_path}: Expected {expected_md5}, got {actual_md5}")
            await handle_modified_file(actual_file_path, expected_md5, reader, writer)
        else:
            logger.info(f"File verified: {actual_file_path}")

    paths = [Path(file_path) for file_path in directory_dict.keys()]
    for root, dirs, files in os.walk(dir_path):
        for curr_file in files:
            relative_path = os.path.relpath(os.path.join(root, curr_file), dir_path)
            same_paths = [path for path in paths if path == Path(relative_path)]
            if len(same_paths) == 0:
                logger.warning(f"File exists locally but not in remote: {relative_path}")


async def handle_sync(reader, writer):
    logger.info("handle server sync message")
    data = await reader.readexactly(MESSAGE_LENGTH_FIELD_LENGTH)
    data = await reader.readexactly(struct.unpack(">H", data)[0])
    dir_dict = json.loads(data.decode())
    await verify_directory_contents(dir_dict, ".", reader, writer)


async def tcp_echo_client(host, port):
    reader, writer = await asyncio.open_connection(host, port)

    while True:
        data = await reader.readexactly(MESSAGE_TYPE_LENGTH)
        message_type = int.from_bytes(data)
        logger.info(f'Received message of type: {message_type}')

        if message_type == MessageType.SERVER_SYNC.value:
            await handle_sync(reader, writer)
        else:
            logger.error(f"unrecognizable message code {message_type}")
            break

    logger.info('Close the connection')
    writer.close()
    await writer.wait_closed()


if __name__ == '__main__':
    asyncio.run(tcp_echo_client('localhost', 8888))
