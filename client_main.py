import asyncio

from shared_folder_opu.client import SharedFolderClient
from shared_folder_opu.general_utils import get_directory_path
from shared_folder_opu.logger_singleton import SingletonLogger
from configuration import SERVER_PORT, SERVER_HOST

logger = SingletonLogger.get_logger()


shared_dir_path = get_directory_path()
logger.info(f"The path that we will sync with the shared folder is {shared_dir_path}")

asyncio.run(SharedFolderClient(shared_dir_path, SERVER_HOST, SERVER_PORT).client(), debug=True)
