import asyncio

from shared_folder_opu.general_utils import exception_handler, get_directory_path
from shared_folder_opu.logger_singleton import SingletonLogger
from shared_folder_opu.server import SharedFolderServer
from configuration import SERVER_PORT, SERVER_HOST

logger = SingletonLogger.get_logger()


async def main():
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(exception_handler)

    shared_dir_path = get_directory_path()
    logger.info(f"will share the path {shared_dir_path}")

    shared_folder_server = SharedFolderServer(SERVER_HOST, SERVER_PORT, shared_dir_path)
    await shared_folder_server.run_server()


asyncio.run(main())
