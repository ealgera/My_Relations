import logging
from logging.handlers import RotatingFileHandler
from config import get_settings
import os

settings    = get_settings()
DEVELOPMENT = settings.DEVELOPMENT

def get_log_level():  # DEVELOPMENT or PRODUCTION
    if DEVELOPMENT:
        return logging.DEBUG
    else:
        return logging.ERROR

def setup_logger(name, log_file, level=logging.DEBUG):
    """Function to setup as many loggers as you want"""

    # Zorg ervoor dat de log directory bestaat
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s:%(lineno)d %(message)s')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    # File handler
    file_handler = RotatingFileHandler(log_file, maxBytes=10000000, backupCount=5)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# Gebruik de functie om een logger op te zetten
app_logger = setup_logger('app_logger', 'logs/app.log')

def log_debug(message):
    if DEVELOPMENT:
        app_logger.debug(message)

def log_info(message):
    if DEVELOPMENT:
        app_logger.info(message)

def log_warning(message):
    app_logger.warning(message)

def log_error(message):
    app_logger.error(message)

def log_critical(message):
    app_logger.critical(message)
