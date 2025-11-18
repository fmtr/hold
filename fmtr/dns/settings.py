import asyncio

from fmtr.dns.paths import paths
from fmtr.dns.proxy import AdBlockDoHProxy
from fmtr.tools import sets


class Settings(sets.Base):
    paths = paths
    server: AdBlockDoHProxy

    def run(self):
        super().run()

        from fmtr.tools import debug
        debug.trace()
        from fmtr import tools
        from fmtr.dns.obs import logger
        from fmtr.dns.paths import paths
        from fmtr.dns.version import __version__

        logger.info(f'Launching {paths.name_ns} {__version__=} {tools.get_version()=} from entrypoint.')
        logger.debug(f'{paths.settings.exists()=} {str(paths.settings)=}')

        logger.info(f'Launching server...')
        from fmtr.dns.api import DNS

        asyncio.run(DNS.start(settings.server))


settings = Settings()
settings
