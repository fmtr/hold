from __future__ import annotations

import asyncio
from functools import cached_property

from corio import api, env
from corio.constants import Constants
from fmtr.dns.obs import logger
from fmtr.dns.paths import paths


class DNS(api.Base):
    TITLE = paths.name_ns
    URL_DOCS = '/'
    PORT = api.Base.PORT + paths.metadata.port + (1000*int(env.IS_DEV))

    def __init__(self, dns_server):
        super().__init__()
        self.dns_server = dns_server

    @cached_property
    def ENDPOINTS(self):
        """

        DNS API endpoint classes.

        """
        return [CacheClear, ToggleBlocking, RefreshBlocklist]

    async def launch(self):
        logger.info(self.message)
        await self.server.serve()

    async def load_blocklist(self) -> int:
        """Load the cached blocklist only after DNS is available for cold starts."""
        await self.dns_server.wait_started()
        with logger.span(f'Loading blocklist...'):
            return await asyncio.to_thread(self.dns_server.rewriter.refresh_blocklist)

    @classmethod
    async def start(cls, server):
        self = cls(server)
        await asyncio.gather(
            self.launch(),
            self.dns_server.start(),
            self.load_blocklist(),
        )


class PostEndpoint(api.endpoint.API):
    @property
    def method(self):
        return self.api.app.post


class CacheClear(PostEndpoint):
    """

    Clear DNS cache.

    """

    PATH = '/cache/clear'
    TAGS = 'cache'

    async def run(self) -> int:
        with logger.span(f'Clearing cache...'):
            length = len(self.api.dns_server.cache.keys())
            self.api.dns_server.cache.clear()

        return length


class ToggleBlocking(PostEndpoint):
    """

    Toggle Ad Blocking.

    """

    PATH = '/blocking/toggle'
    TAGS = 'blocking'

    async def run(self) -> bool:
        current = self.api.dns_server.is_block_enabled
        new = not current
        with logger.span(f'Toggling blocking {current} {Constants.ARROW} {new}...'):
            self.api.dns_server.is_block_enabled = new
            self.api.dns_server.cache.clear()

        return new


class RefreshBlocklist(PostEndpoint):
    """

    Refresh Ad Blocking blocklist.

    """

    PATH = '/blocking/refresh'
    TAGS = 'blocking'

    async def run(self) -> int:
        with logger.span(f'Refreshing blocklist...'):
            length = await asyncio.to_thread(
                self.api.dns_server.rewriter.refresh_blocklist,
                clear=True,
            )
            self.api.dns_server.cache.clear()

        return length


if __name__ == '__main__':
    asyncio.run(DNS.start())
