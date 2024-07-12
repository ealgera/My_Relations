import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(name, log_file, level=logging.DEBUG):
    """Function to setup as many loggers as you want"""

    # Zorg ervoor dat de log directory bestaat
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s:%(lineno)d %(message)s')

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

# Test log bericht
# app_logger.debug("Logging is configured and working.")