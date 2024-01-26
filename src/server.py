import asyncio

from logger_singleton import SingletonLogger

logger = SingletonLogger.get_logger()


async def handle_client(reader, writer):
    while True:
        data = await reader.read(100)  # Read up to 100 bytes
        if not data:
            break
        message = data.decode()
        addr = writer.get_extra_info('peername')
        logger.info(f"Received {message} from {addr}")

        # Echo back the received message (you can modify this part as needed)
        writer.write(data)
        await writer.drain()

    # Close the connection
    writer.close()
    await writer.wait_closed()


async def main(host, port):
    server = await asyncio.start_server(handle_client, host, port)
    addr = server.sockets[0].getsockname()
    logger.info(f'Serving on {addr}')

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main('localhost', 8888))
