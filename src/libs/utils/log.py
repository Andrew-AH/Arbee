from datetime import datetime
import inspect
import logging
from logging import Logger
import os


LOG_DIR = f"logs/{datetime.now().strftime('%Y%m%d-%H%M')}"
LOG_FILE_EXTENSION = ".log"

os.makedirs(LOG_DIR, exist_ok=True)

LOG_FORMAT = "%(asctime)s %(levelname)-5s [%(name)s] %(message)s"
formatter = logging.Formatter(LOG_FORMAT)

# Rename WARNING to WARN for reduced verbosity
logging.addLevelName(logging.WARNING, "WARN")


def get_logger(
    name: str | None = None,
    file_name: str | None = None,
    logs_to_file: bool = False,
    logs_to_console: bool = False,
) -> Logger:
    """
    Create and configure a logger, automatically naming it based on the caller’s context.

    If `name` is provided, it will be used as the logger’s name. Otherwise:
    1. If called from within an instance method, the instance’s class name is used.
    2. If called from within a classmethod, the class name is used.
    3. Otherwise, the filename (without extension) of the caller’s module is used.

    Optionally attach handlers:
      • If `logs_to_file` is True, a FileHandler is created.
        – If `file_name` is provided, that name is used.
        – Otherwise, the resolved logger name is used as the file name.
        – The file is placed under LOG_DIR.
      • If `logs_to_console` is True, a StreamHandler is attached for console output.
    """

    stack = inspect.stack()
    caller_frame = stack[1].frame
    local_vars = caller_frame.f_locals

    # 1. Use provided name
    if name:
        logger_name = name

    # 2. Inside class instance
    elif "self" in local_vars:
        logger_name = local_vars["self"].__class__.__name__

    # 3. Inside class
    elif "cls" in local_vars:
        logger_name = local_vars["cls"].__name__

    # 4. Fallback to file name
    else:
        logger_name = os.path.basename(caller_frame.f_code.co_filename)[
            :-3
        ]  # trim off .py

    handlers = []

    if logs_to_file:
        if file_name:
            log_file_name = file_name + LOG_FILE_EXTENSION

        else:
            log_file_name = logger_name + LOG_FILE_EXTENSION

        file_handler = logging.FileHandler(
            filename=os.path.join(LOG_DIR, log_file_name), delay=True
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    if logs_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)

    logger = logging.getLogger(logger_name)

    # Clear existing handlers to prevent duplicate logs
    logger.handlers.clear()

    for handler in handlers:
        logger.addHandler(handler)

    logger.setLevel(logging.DEBUG)
    return logger
