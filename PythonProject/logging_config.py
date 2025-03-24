import logging

def configure_logging():
    logger = logging.getLogger()
    if not logger.hasHandlers():
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def get_logger(name):
    configure_logging()
    return logging.getLogger(name)
