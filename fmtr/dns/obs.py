from fmtr.tools import logging, debug
from fmtr.tools.environment_tools import IS_DEBUG

from fmtr.dns.version import __version__

debug.trace()

NAME = 'fmtr.dns'

logger = logging.get_logger(
    name=NAME,
    stream=logging.DEVELOPMENT if IS_DEBUG else NAME,
    version=__version__,
)
