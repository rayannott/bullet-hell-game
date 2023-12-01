import logging
from typing import Literal

from config.front import *
from config.back import *


def setup_logging(level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = 'WARNING'):
    LEVEL_MAP = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    logging.basicConfig(
        filename='basic.log',
        encoding='utf-8', 
        filemode='a',
        format='%(levelname)s - %(asctime)s - %(filename)s - %(message)s', level=LEVEL_MAP[level]
    )
