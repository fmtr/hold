from fmtr.dns.paths import paths
from fmtr.dns.version import __version__
from fmtr.tools import logging, debug, Constants

debug.trace()

logger = logging.get_logger(
    name=paths.name_ns,
    stream=Constants.INFRA,
    version=__version__,
)
