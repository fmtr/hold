from dataclasses import dataclass
from typing import List

from fmtr.dns.transformer import RuleUpstream, KeyDNS
from fmtr.tools import dns, patterns


@dataclass
class Upstreams(patterns.Transformer):
    items: List[RuleUpstream]
    default: dns.client.HTTP

    def resolve(self, exchange: dns.dm.Exchange):
        """

        Select the appropriate upstream resolver based on the question plus rules

        """

        key = KeyDNS.from_exchange(exchange)
        upstream = self.get(key)
        return upstream.resolve(exchange)
