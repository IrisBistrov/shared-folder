import asyncio
import struct

from logger_singleton import SingletonLogger
from directory_utils import directory_to_json
from protocol import ServerSyncMessage, MESSAGE_TYPE_LENGTH, MessageType
from server_handlers import handle_user_edit, handle_user_request
from general_utils import get_directory_path, exception_handler

logger = SingletonLogger.get_logger()

MESSAGE_TYPE_TO_HANDLER = {
    MessageType.USER_EDIT.value: handle_user_edit,
    MessageType.USER_REQUEST.value: handle_user_request
}

global shared_dir_path


async def handle_client(reader, writer):
    writer.write(ServerSyncMessage(directory_to_json(shared_dir_path).encode()).pack())
    await writer.drain()

    while True:
        data = await reader.readexactly(MESSAGE_TYPE_LENGTH)
        message_type = struct.unpack(">B", data)[0]
        logger.info(f"received message of type: {message_type}")
        await MESSAGE_TYPE_TO_HANDLER[message_type](reader, writer, shared_dir_path)


async def main(host, port):
    server = await asyncio.start_server(handle_client, host, port)
    addr = server.sockets[0].getsockname()
    logger.info(f'Serving on {addr}')

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(exception_handler)
    shared_dir_path = get_directory_path()
    logger.info(f"will share the path {shared_dir_path}")

    asyncio.run(main('localhost', 8080), debug=True)
