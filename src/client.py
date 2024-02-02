import asyncio
import contextlib
import json
import os
import struct
from pathlib import Path

from watchdog.observers import Observer

from directory_utils import calculate_file_md5, calculate_md5sum
from folder_monitor import MyHandler
from general_utils import get_directory_path, get_string, get_local_file_path
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
        self.file_requests = {}

    @contextlib.contextmanager
    def disable_observer(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()

        yield

        if self.observer:
            my_loop = asyncio.get_running_loop()
            self.start_new_observer(my_loop)

    async def handle_missing_file(self, missing_file_path: str, missing_hash: str):
        logger.info(f"add {missing_file_path}: {missing_hash} to file requests")
        self.file_requests[os.path.join(self.shared_dir_path, missing_file_path).encode()] = missing_hash.encode()

        self.writer.write(UserRequestMessage(missing_file_path, missing_hash).pack())
        await self.writer.drain()

    async def handle_server_file(self):
        missing_file_path = await get_local_file_path(self.reader, self.shared_dir_path.encode())

        content = await get_string(self.reader)
        md5sum = await self.reader.readexactly(32)

        if missing_file_path not in self.file_requests.keys():
            logger.warning(f"{missing_file_path} not in file requests {self.file_requests.keys()}")
            return

        if calculate_md5sum(content).encode() != md5sum:
            logger.info("received outdated version, wait for another message")
            return

        self.file_requests.pop(missing_file_path)
        logger.info(f"got the content of {missing_file_path}")
        with self.disable_observer():
            os.makedirs(os.path.dirname(missing_file_path), exist_ok=True)
            with open(os.path.join(self.shared_dir_path.encode(), missing_file_path), "wb") as f:
                f.write(content)

    async def handle_modified_file(self, actual_file_path: str, expected_md5: str):
        logger.info(f"MD5 mismatch for {actual_file_path}: Expected {expected_md5}")
        await self.handle_missing_file(actual_file_path, expected_md5)

        with self.disable_observer():
            os.unlink(os.path.join(self.shared_dir_path, actual_file_path))

    async def verify_remote_files(self, directory_dict: dict[str: str]):
        logger.info("verifying that all remote files are equal to local")

        for file_path, expected_md5 in directory_dict.items():
            actual_file_path = os.path.join(self.shared_dir_path, file_path)
            logger.info(f"verifying {actual_file_path}")

            if not os.path.exists(actual_file_path):
                await self.handle_missing_file(os.path.relpath(actual_file_path, self.shared_dir_path), expected_md5)
                continue

            actual_md5 = calculate_file_md5(actual_file_path)
            if actual_md5 != expected_md5:
                await self.handle_modified_file(os.path.relpath(actual_file_path, self.shared_dir_path), expected_md5)
            else:
                logger.info(f"file verified: {actual_file_path}")

    async def verify_local_files(self, directory_dict: dict[str: str]):
        logger.info("verifying no redundant local files")

        paths = [Path(file_path) for file_path in directory_dict.keys()]
        for root, dirs, files in os.walk(self.shared_dir_path):
            for curr_file in files:
                full_path = os.path.join(root, curr_file)
                relative_path = os.path.relpath(full_path, self.shared_dir_path)
                same_paths = [path for path in paths if path == Path(relative_path)]
                if len(same_paths) == 0:
                    logger.info(f"File exists locally but not in remote: {relative_path}")
                    with self.disable_observer():
                        os.unlink(full_path)

    async def verify_directory_contents(self, directory_dict: dict[str: str]):
        await asyncio.gather(
            self.verify_local_files(directory_dict),
            self.verify_remote_files(directory_dict)
        )

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
            match message_type:
                case MessageType.SERVER_SYNC.value:
                    await self.handle_sync()
                case MessageType.SERVER_FILE.value:
                    await self.handle_server_file()
                case _:
                    logger.error(f"unrecognizable message code {message_type}")

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
            client_task = asyncio.create_task(self.client_flow())
            await client_task
            if client_task.exception():
                logger.error(client_task.exception())
                if self.observer.is_alive:
                    self.observer.stop()
                    self.observer.join()
                break
            await asyncio.sleep(0.1)


# global shared_dir_path
shared_dir_path = get_directory_path()
logger.info(f"The path that we will sync with the shared folder is {shared_dir_path}")

asyncio.run(SharedFolderClient(shared_dir_path, "localhost", 8080).client(), debug=True)
