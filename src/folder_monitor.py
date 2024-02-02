import os
from asyncio import StreamReader, StreamWriter, run, Lock, run_coroutine_threadsafe

from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent, \
    DirModifiedEvent

from logger_singleton import SingletonLogger
from protocol import UserEditMessage, UserEditTypes, Message

logger = SingletonLogger.get_logger()


class MyHandler(FileSystemEventHandler):

    def __init__(self, reader: StreamReader, writer: StreamWriter, shared_folder: str, reading_lock: Lock, loop):
        self.loop = loop
        self.reading_lock = reading_lock
        self.shared_folder = shared_folder
        self.writer = writer
        self.reader = reader

    async def handle_communication(self, request: Message):
        async with self.reading_lock:
            self.writer.write(request.pack())
            await self.writer.drain()

    def on_modified(self, event: FileModifiedEvent | DirModifiedEvent):
        logger.info(f'File {event.src_path} has been modified')

        if type(event) == DirModifiedEvent:
            return

        relative_path = os.path.relpath(event.src_path, self.shared_folder)
        with open(event.src_path, "rb") as new_file:
            content = new_file.read()
        future = run_coroutine_threadsafe(
            self.handle_communication(UserEditMessage(UserEditTypes.MODIFY, relative_path.encode(), content)),
            self.loop
        )
        return future.result()

    def on_created(self, event: FileCreatedEvent):
        logger.info(f'File {event.src_path} has been created')
        relative_path = os.path.relpath(event.src_path, self.shared_folder)
        future = run_coroutine_threadsafe(
            self.handle_communication(UserEditMessage(UserEditTypes.CREATE, relative_path.encode())),
            self.loop
        )
        future.result()

    def on_deleted(self, event: FileDeletedEvent):
        logger.info(f'File {event.src_path} has been deleted')
        relative_path = os.path.relpath(event.src_path, self.shared_folder)
        future = run_coroutine_threadsafe(
            self.handle_communication(UserEditMessage(UserEditTypes.DELETE, relative_path.encode())),
            self.loop
        )
        future.result()
