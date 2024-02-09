import asyncio

from shared_folder_opu.client import SharedFolderClient
from shared_folder_opu.general_utils import get_directory_path
from shared_folder_opu.logger_singleton import SingletonLogger

logger = SingletonLogger.get_logger()


shared_dir_path = get_directory_path()
logger.info(f"The path that we will sync with the shared folder is {shared_dir_path}")

asyncio.run(SharedFolderClient(shared_dir_path, "localhost", 8080).client(), debug=True)
