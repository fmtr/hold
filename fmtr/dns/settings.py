import asyncio

import corio
from corio import sets
from fmtr.dns.paths import paths
from fmtr.dns.proxy import AdBlockDoHProxy


class Settings(sets.Base):
    paths = paths
    server: AdBlockDoHProxy

    def run(self):
        super().run()

        from corio import debug
        debug.trace()
        from fmtr.dns.obs import logger
        from fmtr.dns.paths import paths

        logger.info(f'Launching {paths.name_ns} {paths.metadata.version=} {corio.get_version()=} from entrypoint.')
        logger.debug(f'{paths.settings.exists()=} {str(paths.settings)=}')

        logger.info(f'Launching server...')
        from fmtr.dns.api import DNS

        asyncio.run(DNS.start(settings.server))


settings = Settings()
settings
