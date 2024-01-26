import asyncio

from logger_singleton import SingletonLogger
from directory_utils import directory_to_json
from protocol import ServerSyncMessage, MESSAGE_TYPE_LENGTH, MessageType
from server_handlers import handle_user_edit, handle_user_request

logger = SingletonLogger.get_logger()

MESSAGE_TYPE_TO_HANDLER = {
    MessageType.USER_EDIT.value: handle_user_edit,
    MessageType.USER_REQUEST.value: handle_user_request
}


async def handle_client(reader, writer):
    writer.write(ServerSyncMessage(directory_to_json(".").encode()).pack())

    while True:
        message_type = await reader.read(MESSAGE_TYPE_LENGTH)
        MESSAGE_TYPE_TO_HANDLER[message_type]()


async def main(host, port):
    server = await asyncio.start_server(handle_client, host, port)
    addr = server.sockets[0].getsockname()
    logger.info(f'Serving on {addr}')

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main('localhost', 8888))
