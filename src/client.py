import asyncio

from logger_singleton import SingletonLogger

logger = SingletonLogger.get_logger()


async def tcp_echo_client(message, host, port):
    reader, writer = await asyncio.open_connection(host, port)

    logger.info(f'Send: {message}')
    writer.write(message.encode())

    data = await reader.read(100)
    logger.info(f'Received: {data.decode()}')

    logger.info('Close the connection')
    writer.close()
    await writer.wait_closed()


if __name__ == '__main__':
    asyncio.run(tcp_echo_client('Hello World!', 'localhost', 8888))
