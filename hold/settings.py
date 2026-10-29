import asyncio
from functools import cached_property

import corio
from corio import caching, sets, Path

from hold.paths import paths
from hold.proxy import AdBlockDoHProxy



class Settings(sets.Base,cli_parse_args=True):
    paths = paths
    cache: Path|None=paths.cache
    server: AdBlockDoHProxy

    @cached_property
    def disk(self):
        return caching.Disk(self.cache)

    async def run(self):
        await super().run()

        from corio import debug
        debug.trace()
        from hold.obs import logger
        from hold.paths import paths

        self.server.rewriter.blocklist.disk = self.disk

        logger.info(f'Launching {paths.name} {paths.metadata.version=} {corio.get_version()=} from entrypoint.')
        logger.debug(f'{paths.settings.exists()=} {str(paths.settings)=}')

        logger.info(f'Launching server...')
        from hold.api import DNS

        try:
            await DNS.start(settings.server)
        except KeyboardInterrupt:
            logger.info(f'Closed {paths.name}.')



settings = Settings()
settings
