import asyncio
import uvicorn

from corio import api
from corio.constants import Constants
from fmtr.dns.obs import logger
from fmtr.dns.paths import paths


class DNS(api.Base):
    TITLE = paths.name_ns
    URL_DOCS = '/'

    def __init__(self, dns_server):
        super().__init__()
        self.dns_server = dns_server

    def get_endpoints(self):
        """

        Define endpoints

        """
        endpoints = [
            api.Endpoint(method=self.cache_clear, path='/cache/clear', method_http=self.app.post, tags='cache'),
            api.Endpoint(method=self.toggle_blocking, path='/blocking/toggle', method_http=self.app.post, tags='blocking'),
            api.Endpoint(method=self.refresh_blocklist, path='/blocking/refresh', method_http=self.app.post, tags='blocking'),

        ]

        return endpoints

    def cache_clear(self) -> int:
        """

        Clear DNS cache.

        """
        with logger.span(f'Clearing cache...'):
            length = len(self.dns_server.cache.keys())
            self.dns_server.cache.clear()

        return length

    def toggle_blocking(self) -> bool:
        """

        Toggle Ad Blocking.

        """

        currrent = self.dns_server.is_block_enabled
        new = not currrent
        with logger.span(f'Toggling blocking {currrent} {Constants.ARROW} {new}...'):
            self.dns_server.is_block_enabled = new
            self.cache_clear()

        return new

    def refresh_blocklist(self) -> int:
        """

        Refresh Ad Blocking blocklist.

        """
        with logger.span(f'Refreshing blocklist...'):
            self.dns_server.rewriter.refresh_blocklist()
            length = len(self.dns_server.rewriter.blocklist.refresh())
            self.dns_server.cache.clear()

        return length

    async def launch(self):
        config = uvicorn.Config(self.app, host=self.HOST, port=self.PORT)
        api = uvicorn.Server(config)
        await api.serve()

    @classmethod
    async def start(cls, server):
        self = cls(server)
        await asyncio.gather(
            self.launch(),
            self.dns_server.start(),
        )


if __name__ == '__main__':
    asyncio.run(DNS.start())
