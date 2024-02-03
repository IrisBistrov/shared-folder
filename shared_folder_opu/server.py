import asyncio
import struct
from asyncio import wait_for, StreamReader, StreamWriter

from shared_folder_opu.logger_singleton import SingletonLogger
from shared_folder_opu.directory_utils import directory_to_json
from shared_folder_opu.protocol import ServerSyncMessage, MESSAGE_TYPE_LENGTH, MessageType, Message
from shared_folder_opu.server_handlers import handle_user_edit, handle_user_request
from shared_folder_opu.general_utils import get_directory_path, exception_handler

logger = SingletonLogger.get_logger()


class SharedFolderServer:
    def __init__(self, host, port, shared_dir_path):
        self.host = host
        self.port = port
        self.shared_dir_path = shared_dir_path
        self.clients = []  # List to keep track of connected clients

    async def broadcast(self, message: Message):
        logger.debug(f"send broadcast to {len(self.clients)} clients")
        for client in self.clients:
            client.write(message.pack())
            await client.drain()

    async def handle_message(self, message: MessageType, reader: StreamReader, writer: StreamWriter):

        match message:
            case MessageType.USER_EDIT:
                await handle_user_edit(reader, self.shared_dir_path)
                await self.broadcast(ServerSyncMessage(directory_to_json(self.shared_dir_path).encode()))
            case MessageType.USER_REQUEST:
                await handle_user_request(reader, writer, self.shared_dir_path)
            case _:
                logger.error(f"received invalid message type {message.name}")

    async def _handle_client(self, reader: StreamReader, writer: StreamWriter):
        self.clients.append(writer)  # Add client to clients list
        writer.write(ServerSyncMessage(directory_to_json(self.shared_dir_path).encode()).pack())
        await writer.drain()

        try:
            while True:
                await asyncio.sleep(0.1)

                try:
                    data = await wait_for(reader.readexactly(MESSAGE_TYPE_LENGTH), timeout=0.01)
                except asyncio.TimeoutError:
                    continue
                message_type = MessageType(struct.unpack(">B", data)[0])
                logger.debug(f"received message of type: {message_type.name}")
                await self.handle_message(message_type, reader, writer)

        finally:
            logger.info("client disconnected")
            self.clients.remove(writer)  # Remove client from clients list
            writer.close()
            await writer.wait_closed()

    async def handle_client(self, reader: StreamReader, writer: StreamWriter):
        task = asyncio.create_task(self._handle_client(reader, writer))
        await task
        if task.exception():
            logger.error(task.exception())

    async def run_server(self):
        server = await asyncio.start_server(
            self.handle_client, self.host, self.port)
        async with server:
            await server.serve_forever()


async def main():
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(exception_handler)

    shared_dir_path = get_directory_path()
    logger.info(f"will share the path {shared_dir_path}")

    # TODO: read from config file
    shared_folder_server = SharedFolderServer("localhost", 8080, shared_dir_path)
    await shared_folder_server.run_server()


asyncio.run(main())
