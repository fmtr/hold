from dataclasses import dataclass
from typing import List

from corio import dns, patterns
from fmtr.dns.transformer import RuleUpstream, KeyDNS


@dataclass
class Upstreams(patterns.Transformer):
    items: List[RuleUpstream]
    default: dns.client.HTTP

    async def resolve(self, exchange: dns.dm.Exchange):
        """

        Select the appropriate upstream resolver based on the question plus rules

        """

        key = KeyDNS.from_exchange(exchange)
        upstream = self.get(key)
        return await upstream.resolve(exchange)

    async def aclose(self):
        await self.default.aclose()
        for item in self.items:
            await item.target.aclose()
