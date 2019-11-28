import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logging_format = '%(asctime)s: %(message)s'
formatter = logging.Formatter(fmt=logging_format, datefmt='%H:%M:%S')

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)


# logging.basicConfig(
#     format=logging_format, level=logging.DEBUG, datefmt='%H:%M:%S')
