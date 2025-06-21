import asyncio
import uvicorn

from fmtr.dns.obs import logger
from fmtr.dns.paths import paths
from fmtr.tools import api
from fmtr.tools.constants import Constants


class DNS(api.ApiBase):
    TITLE = paths.name_ns

    def __init__(self, server):
        super().__init__()
        self.server = server

    def get_endpoints(self):
        """

        Define endpoints

        """
        endpoints = [
            api.Endpoint(method=self.cache_clear, path='/cache/clear', method_http=self.app.post, tags='cache'),
            api.Endpoint(method=self.toggle_blocking, path='/blocking/toggle', method_http=self.app.post, tags='blocking'),

        ]

        return endpoints

    def cache_clear(self) -> int:
        """

        Clear DNS cache.

        """
        with logger.span(f'Clearing cache...'):
            length = len(self.server.cache.keys())
            self.server.cache.clear()

        return length

    def toggle_blocking(self) -> bool:
        """

        Toggle Ad Blocking.

        """

        currrent = self.server.is_block_enabled
        new = not currrent
        with logger.span(f'Toggling blocking {currrent} {Constants.ARROW} {new}...'):
            self.server.is_block_enabled = new
            self.cache_clear()

        return new

    async def launch(self):
        config = uvicorn.Config(self.app, host=self.HOST, port=self.PORT)
        api = uvicorn.Server(config)
        await api.serve()

    @classmethod
    async def start(cls, server):
        self = cls(server)
        await asyncio.gather(
            self.launch(),
            self.server.start(),
        )


if __name__ == '__main__':
    asyncio.run(DNS.start())
