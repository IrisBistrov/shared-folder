import pyinotify
import asyncio

from logger_singleton import SingletonLogger

logger = SingletonLogger.get_logger()


class InotifyWatcher:
    def __init__(self, directory_to_watch):
        self.directory_to_watch = directory_to_watch
        self.wm = pyinotify.WatchManager()
        self.loop = asyncio.get_event_loop()
        self.notifier = pyinotify.AsyncioNotifier(self.wm, self.loop, default_proc_fun=EventHandler())

    def start(self):
        self.wm.add_watch(self.directory_to_watch, pyinotify.ALL_EVENTS)
        logger.info(f"Started monitoring {self.directory_to_watch}")

    def stop(self):
        self.notifier.stop()
        logger.info(f"Stopped monitoring {self.directory_to_watch}")


class EventHandler(pyinotify.ProcessEvent):
    def process_default(self, event):
        logger.info(f"Event: {event.maskname} on path: {event.pathname}")


async def async_main():
    watcher = InotifyWatcher('/tmp')  # Replace with the path you want to monitor
    watcher.start()

    try:
        await asyncio.Event().wait()  # Keep running until interrupted
    finally:
        watcher.stop()

