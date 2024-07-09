import logging
import logging.config
from datetime import datetime
import os
import sys
from colorama import Fore, Style, init

init(autoreset=True)


class ColorHandler(logging.StreamHandler):
    def emit(self, record):
        color = {
            logging.DEBUG: Fore.BLUE,
            logging.INFO: Fore.GREEN,
            logging.WARNING: Fore.YELLOW,
            logging.ERROR: Fore.RED,
            logging.CRITICAL: Fore.RED + Style.BRIGHT
        }.get(record.levelno, Fore.WHITE)
        record.msg = color + record.msg + Style.RESET_ALL
        if isinstance(record.msg, str):
            record.msg = record.msg.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        super().emit(record)


class PlainTextFormatter(logging.Formatter):
    def format(self, record):
        record.msg = record.msg.replace(Fore.GREEN, '').replace(Style.RESET_ALL, '')
        return super().format(record)


LOGFILE = '/tmp/{0}.{1}.log'.format(
    os.path.basename(__file__),
    datetime.now().strftime('%Y%m%dT%H%M%S'))
os.makedirs(os.path.dirname(LOGFILE), exist_ok=True)
DEFAULT_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(levelname)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'plain': {
            '()': PlainTextFormatter,
            'format': '%(asctime)s %(levelname)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            '()': ColorHandler,
            'formatter': 'plain',
            'level': 'INFO',
            'stream': sys.stdout,

        },
        'file': {
            'class': 'logging.FileHandler',
            'formatter': 'plain',
            'level': 'DEBUG',
            'filename': LOGFILE,
            'mode': 'w',
            'encoding': 'utf8',
        },
    },
    'loggers': {
        '': {
            'level': 'INFO',
            'handlers': ['console', 'file']
        },
        __name__: {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': False,
        },
    }
}

logging.config.dictConfig(DEFAULT_LOGGING)
logger = logging.getLogger(__name__)
