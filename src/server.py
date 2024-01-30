import asyncio
import struct
from asyncio import Lock, wait_for

from logger_singleton import SingletonLogger
from directory_utils import directory_to_json
from protocol import ServerSyncMessage, MESSAGE_TYPE_LENGTH, MessageType, Message
from server_handlers import handle_user_edit, handle_user_request
from general_utils import get_directory_path, exception_handler

logger = SingletonLogger.get_logger()

MESSAGE_TYPE_TO_HANDLER = {
    MessageType.USER_EDIT: handle_user_edit,
    MessageType.USER_REQUEST: handle_user_request
}

global shared_dir_path


class SharedFolderServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.lock = Lock()
        self.clients = []  # List to keep track of connected clients

    async def broadcast(self, message: Message):
        logger.info(f"clients are {self.clients}")
        for client in self.clients:
            client.write(message.pack())
            await client.drain()

    async def handle_client(self, reader, writer):
        self.clients.append(writer)  # Add client to clients list
        writer.write(ServerSyncMessage(directory_to_json(shared_dir_path).encode()).pack())
        await writer.drain()

        try:
            while True:
                await asyncio.sleep(0.1)

                async with self.lock:
                    try:
                        data = await wait_for(reader.readexactly(MESSAGE_TYPE_LENGTH), timeout=0.01)
                    except asyncio.TimeoutError:
                        continue
                    message_type = MessageType(struct.unpack(">B", data)[0])
                    logger.info(f"received message of type: {message_type.name}")
                    await MESSAGE_TYPE_TO_HANDLER[message_type](reader, writer, shared_dir_path)
                    if message_type == MessageType.USER_EDIT:
                        await self.broadcast(ServerSyncMessage(directory_to_json(shared_dir_path).encode()))
        finally:
            logger.info("client disconnected")
            writer.close()
            await writer.wait_closed()
            self.clients.remove(writer)  # Remove client from clients list

    async def run_server(self):
        server = await asyncio.start_server(
            self.handle_client, self.host, self.port)
        async with server:
            await server.serve_forever()


async def main():
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(exception_handler)

    global shared_dir_path
    shared_dir_path = get_directory_path()
    logger.info(f"will share the path {shared_dir_path}")

    shared_folder_server = SharedFolderServer("localhost", 8080)
    await shared_folder_server.run_server()

asyncio.run(main())
