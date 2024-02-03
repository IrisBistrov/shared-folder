import logging
from rich.logging import RichHandler


class SingletonLogger:
    _logger = None

    @staticmethod
    def get_logger():
        if SingletonLogger._logger is None:
            SingletonLogger._logger = logging.getLogger("rich")
            SingletonLogger._logger.setLevel(logging.DEBUG)
            handler = RichHandler(tracebacks_show_locals=True, rich_tracebacks=True)
            formatter = logging.Formatter('%(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            SingletonLogger._logger.addHandler(handler)
        return SingletonLogger._logger
