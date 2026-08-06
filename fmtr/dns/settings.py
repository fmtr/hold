import asyncio
from functools import cached_property

import corio
from corio import caching, sets, Path

from fmtr.dns.paths import paths
from fmtr.dns.proxy import AdBlockDoHProxy



class Settings(sets.Base,cli_parse_args=True):
    paths = paths
    cache: Path|None=paths.cache
    server: AdBlockDoHProxy

    @cached_property
    def disk(self):
        return caching.Disk(self.cache)

    def run(self):
        super().run()

        from corio import debug
        debug.trace()
        from fmtr.dns.obs import logger
        from fmtr.dns.paths import paths

        self.server.rewriter.blocklist.bind_disk(self.disk)

        logger.info(f'Launching {paths.name_ns} {paths.metadata.version=} {corio.get_version()=} from entrypoint.')
        logger.debug(f'{paths.settings.exists()=} {str(paths.settings)=}')

        logger.info(f'Launching server...')
        from fmtr.dns.api import DNS

        try:
            asyncio.run(DNS.start(settings.server))
        except KeyboardInterrupt:
            logger.info(f'Closed {paths.name_ns}.')



settings = Settings()
settings
