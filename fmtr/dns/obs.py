from fmtr.dns.paths import paths
from fmtr.dns.version import __version__
from fmtr.tools import logging, debug

debug.trace()



logger = logging.get_logger(
    name=paths.name_ns,
    stream=paths.name_ns,
    version=__version__,
)
