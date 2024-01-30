import asyncio
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

    def __init__(self, folder_path: str, host: str, port: int):
        self.port = port
        self.host = host
        self.shared_dir_path = folder_path
        self.lock = asyncio.Lock()
        self.observer = None
        self.event_handler = None
        self.reader = None
        self.writer = None

    async def handle_missing_file(self, missing_file_path: str, missing_hash: str):
        logger.info(f"file missing: {missing_file_path} with hash {missing_hash}")
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

    async def handle_modified_file(self, actual_file_path: str, expected_md5: str):
        logger.info(f"MD5 mismatch for {actual_file_path}: Expected {expected_md5}, got {actual_md5}")
        os.unlink(actual_file_path)
        await self.handle_missing_file(actual_file_path, expected_md5)

    async def verify_directory_contents(self, directory_dict: dict):
        for file_path, expected_md5 in directory_dict.items():
            actual_file_path = os.path.join(self.shared_dir_path, file_path)

            if not os.path.exists(actual_file_path):
                relative_path = os.path.relpath(actual_file_path, self.shared_dir_path)
                await self.handle_missing_file(relative_path, expected_md5)
                continue

            actual_md5 = calculate_md5(actual_file_path)
            if actual_md5 != expected_md5:
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

    async def client_flow(self):
        async with self.lock:
            try:
                data = await asyncio.wait_for(self.reader.readexactly(MESSAGE_TYPE_LENGTH), timeout=0.3)
            except asyncio.TimeoutError:
                return

            message_type = struct.unpack(">B", data)[0]
            logger.info(f'Received message of type: {message_type}')

            if message_type != MessageType.SERVER_SYNC.value:
                logger.error(f"unrecognizable message code {message_type}")
                return

            if self.observer:
                logger.info("stop observer")
                self.observer.stop()

            await self.handle_sync()

    def start_new_observer(self, my_loop):
        logger.info("start new observer")
        self.observer = Observer()
        self.event_handler = MyHandler(self.reader, self.writer, self.shared_dir_path, self.lock, my_loop)
        self.observer.schedule(self.event_handler, self.shared_dir_path, recursive=True)
        self.observer.start()

    async def client(self):
        my_loop = asyncio.get_running_loop()
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        await self.client_flow()
        self.start_new_observer(my_loop)

        while True:
            if not self.observer.is_alive():
                self.start_new_observer(my_loop)

            await self.client_flow()
            await asyncio.sleep(1)


loop = asyncio.get_event_loop()
loop.set_debug(True)
loop.set_exception_handler(exception_handler)

# global shared_dir_path
shared_dir_path = get_directory_path()
logger.info(f"The path that we will sync with the shared folder is {shared_dir_path}")

asyncio.run(SharedFolderClient(shared_dir_path, "localhost", 8080).client())
