import os
import logging
from colorlog import ColoredFormatter
from  datetime import *

log_file_enable = True

def get_logger():
    """Return a logger with a default ColoredFormatter."""
    formatter = ColoredFormatter(
        "%(log_color)s[%(levelname)-8s] [%(filename)s:%(lineno)d]: %(log_color)s%(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'bold_red',
        }
    )

    logger = logging.getLogger('boxofficesite')
    #add handler at first time call
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)

        s_handler = logging.StreamHandler()
        s_handler.setFormatter(formatter)
        s_handler.setLevel(logging.DEBUG)
        logger.addHandler(s_handler)

        f_handler = logging.FileHandler(os.path.join('log', '{}.log'.format(datetime.now().strftime('%y%m%d.%H%M%S'))))
        f_handler.setFormatter(formatter)
        f_handler.setLevel(logging.DEBUG)
        logger.addHandler(f_handler)

    return logger

def log_file(content, filename):
    if not log_file_enable:
        return

    with open(os.path.join("log", filename), "w") as f:
        f.write(content)

log = get_logger()
