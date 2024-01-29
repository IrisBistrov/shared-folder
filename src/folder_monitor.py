from watchdog.events import FileSystemEventHandler

from logger_singleton import SingletonLogger

logger = SingletonLogger.get_logger()


class MyHandler(FileSystemEventHandler):

    def on_modified(self, event):
        logger.info(f'File {event.src_path} has been modified')

    def on_created(self, event):
        logger.info(f'File {event.src_path} has been created')

    def on_deleted(self, event):
        logger.info(f'File {event.src_path} has been deleted')

