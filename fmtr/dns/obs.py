from corio import logs, debug, Constants
from fmtr.dns.paths import paths

debug.trace()

logger = logs.get_logger(
    name=paths.name_ns,
    stream=Constants.INFRA,
    version=paths.metadata.version,
)
