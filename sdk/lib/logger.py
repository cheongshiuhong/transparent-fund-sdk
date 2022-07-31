# Libraries
import logging

# Constants
MESSAGE_FORMAT = (
    "[%(levelname)-5s | %(asctime)s] SDK:%(name)s:L%(lineno)d:%(funcName)s: %(message)s"
)
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


class SdkLogger(logging.Logger):
    """
    Logger class inheriting from python's native logger.
    """

    def __init__(self, name: str, level: int = logging.INFO):
        super().__init__(name)

        # Console logger
        console_formatter = logging.Formatter(MESSAGE_FORMAT, datefmt=DATE_FORMAT)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)

        self.setLevel(level)
        self.addHandler(console_handler)
