import os
import logging
from logging.handlers import RotatingFileHandler


LOG_DIR=os.getenv("LOG_DIR", "logs")
LOG_FILE=os.getenv("LOG_FILE", "dropit.log")

os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger(name:str = "dropit") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    file_handler = RotatingFileHandler(os.path.join(LOG_DIR, LOG_FILE), maxBytes=1000000, backupCount=5)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    if not logger.hasHandlers():
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger