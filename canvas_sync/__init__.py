import logging

logging_format = '%(asctime)s: %(message)s'
logging.basicConfig(
    format=logging_format, level=logging.DEBUG, datefmt='%H:%M:%S')
