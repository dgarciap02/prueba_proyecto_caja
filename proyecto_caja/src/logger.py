import logging
from rich.logging import RichHandler
from os import getenv
from datetime import datetime


logger = logging.getLogger(__name__)

# the handler determines where the logs go: stdout/file
shell_handler = RichHandler(markup=True)
timestamp = datetime.now().strftime('%Y_%m_%d_%M_%S')
file_handler = logging.FileHandler("/logs/{}_main.log".format(timestamp))

logger.setLevel(getenv('LOGLEVEL'))
shell_handler.setLevel(getenv('LOGLEVEL'))
file_handler.setLevel(getenv('LOGLEVEL'))

# the formatter determines what our logs will look like
fmt_shell = '%(message)s'
fmt_file = '%(levelname)s %(asctime)s [%(filename)s:%(funcName)s:%(lineno)d] %(message)s'

shell_formatter = logging.Formatter(fmt_shell)
file_formatter = logging.Formatter(fmt_file)

# here we hook everything together
shell_handler.setFormatter(shell_formatter)
file_handler.setFormatter(file_formatter)

logger.addHandler(shell_handler)
logger.addHandler(file_handler)
logger.propagate = False
