import logging
import sys

# create logger object
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create file handler
fh = logging.FileHandler('app.log')
fh.setLevel(logging.DEBUG)

#console handler
c_log_handler = logging.StreamHandler(sys.stdout)
c_log_handler.setLevel(logging.DEBUG)

# create formatter and add it to the file handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
c_log_handler.setFormatter(formatter)

# add the file handler to logger object
logger.addHandler(fh)
logger.addHandler(c_log_handler)