from corio import logs, debug, Constants
from hold.paths import paths

debug.trace()

logger = logs.get_logger(
    name=paths.name,
    stream=Constants.INFRA,
    version=paths.metadata.version,
)
