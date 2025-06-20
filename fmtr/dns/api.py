import asyncio
import uvicorn

from fmtr.dns.obs import logger
from fmtr.tools import api


class DNS(api.ApiBase):

    def __init__(self, server):
        super().__init__()
        self.server = server

    def get_endpoints(self):
        """

        Define endpoints using a dataclass instance.

        """
        endpoints = [
            api.Endpoint(method=self.clear_cache, path='/clear_cache', method_http=self.app.post)

        ]

        return endpoints

    def clear_cache(self) -> int:
        with logger.span(f'Clearing cache...'):
            length = len(self.server.cache.keys())
            self.server.cache.clear()

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
            self.server.start(),
        )


if __name__ == '__main__':
    asyncio.run(DNS.start())
