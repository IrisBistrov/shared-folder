import asyncio
import contextlib
import json
import os
import struct
from pathlib import Path

from watchdog.observers import Observer

from directory_utils import calculate_md5
from folder_monitor import MyHandler
from general_utils import get_directory_path, get_string, get_local_file_path, exception_handler
from logger_singleton import SingletonLogger
from protocol import MESSAGE_TYPE_LENGTH, MESSAGE_LENGTH_FIELD_LENGTH, MessageType, UserRequestMessage

logger = SingletonLogger.get_logger()


class SharedFolderClient:

    def __init__(self, shared_dir_path: str, host: str, port: int):
        self.port = port
        self.host = host
        self.shared_dir_path = shared_dir_path
        self.observer = Observer()
        self.event_handler = MyHandler()
        self.reader = None
        self.writer = None

    async def handle_missing_file(self, missing_file_path: str, missing_hash: str):
        self.writer.write(UserRequestMessage(missing_file_path, missing_hash).pack())
        await self.writer.drain()
        data = await self.reader.readexactly(MESSAGE_TYPE_LENGTH)
        message_type = struct.unpack(">B", data)[0]
        assert message_type is MessageType.SERVER_FILE.value

        file_path = await get_local_file_path(self.reader, self.shared_dir_path.encode())
        content = await get_string(self.reader)
        md5sum = await self.reader.readexactly(32)

        assert md5sum == missing_hash.encode()
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(os.path.join(self.shared_dir_path, missing_file_path), "wb") as f:
            f.write(content)

    @contextlib.contextmanager
    def dont_observe(self):
        self.observer.stop()
        yield
        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.shared_dir_path, True)
        self.observer.start()

    async def handle_modified_file(self, actual_file_path: str, expected_md5: str):
        os.unlink(actual_file_path)
        await self.handle_missing_file(actual_file_path, expected_md5)

    async def verify_directory_contents(self, directory_dict: dict):
        for file_path, expected_md5 in directory_dict.items():
            actual_file_path = os.path.join(self.shared_dir_path, file_path)

            if not os.path.exists(actual_file_path):
                logger.info(f"file missing: {actual_file_path}")
                relative_path = os.path.relpath(actual_file_path, self.shared_dir_path)
                await self.handle_missing_file(relative_path, expected_md5)
                continue

            actual_md5 = calculate_md5(actual_file_path)
            if actual_md5 != expected_md5:
                logger.info(f"MD5 mismatch for {actual_file_path}: Expected {expected_md5}, got {actual_md5}")
                await self.handle_modified_file(actual_file_path, expected_md5)
            else:
                logger.info(f"file verified: {actual_file_path}")

        paths = [Path(file_path) for file_path in directory_dict.keys()]
        for root, dirs, files in os.walk(self.shared_dir_path):
            for curr_file in files:
                full_path = os.path.join(root, curr_file)
                relative_path = os.path.relpath(full_path, self.shared_dir_path)
                same_paths = [path for path in paths if path == Path(relative_path)]
                if len(same_paths) == 0:
                    logger.info(f"File exists locally but not in remote: {relative_path}")
                    os.unlink(full_path)

    async def handle_sync(self):
        logger.info("handle server sync message")
        data = await self.reader.readexactly(MESSAGE_LENGTH_FIELD_LENGTH)
        data = await self.reader.readexactly(struct.unpack(">H", data)[0])
        dir_dict = json.loads(data.decode())
        logger.info(f"received the dir dict: {dir_dict}")
        await self.verify_directory_contents(dir_dict)

    async def client(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        self.observer.schedule(self.event_handler, self.shared_dir_path, recursive=True)
        self.observer.start()

        while True:
            data = await self.reader.readexactly(MESSAGE_TYPE_LENGTH)
            message_type = struct.unpack(">B", data)[0]
            logger.info(f'Received message of type: {message_type}')

            if message_type != MessageType.SERVER_SYNC.value:
                logger.error(f"unrecognizable message code {message_type}")
                break

            with self.dont_observe():
                await self.handle_sync()


async def main():
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(exception_handler)

    # global shared_dir_path
    shared_dir_path = get_directory_path()
    logger.info(f"The path that we will sync with the shared folder is {shared_dir_path}")

    await SharedFolderClient(shared_dir_path, "localhost", 8080).client()


asyncio.run(main(), debug=True)
