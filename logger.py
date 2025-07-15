import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler


def setup_logging():
    log_filename = os.path.join(datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.log')
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler = RotatingFileHandler(log_filename, maxBytes=1024 * 1024 * 10, encoding='utf-8')
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.DEBUG)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)