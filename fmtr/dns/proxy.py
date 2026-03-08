from dataclasses import dataclass
from functools import cached_property

from corio import dns
from fmtr.dns import caching
from fmtr.dns.client import Upstreams
from fmtr.dns.constants import BLACKHOLE
from fmtr.dns.obs import logger
from fmtr.dns.transformer import KeyDNS, TransformerDNS

Request, Response, Exchange = dns.dm.Request, dns.dm.Response, dns.dm.Exchange


@dataclass(kw_only=True, eq=False)
class AdBlockDoHProxy(dns.proxy.Proxy):
    rewriter: TransformerDNS
    client: Upstreams | dns.client.HTTP
    is_block_enabled: bool = True

    @cached_property
    def cache(self):
        """

        Overridable cache.

        """
        cache = caching.CacheDNS(maxsize=1_024, desc='DNS Request')
        return cache

    def block(self, exchange: Exchange, key: KeyDNS):
        """

        Remove any existing answers, set NXDOMAIN and complete

        """

        logger.warning(f'Request blocked: {key.name} {self.is_block_enabled=}')
        if not self.is_block_enabled:
            return

        exchange.response = Response.from_message(exchange.request.get_response_template())
        exchange.response.message.set_rcode(dns.dns.rcode.NXDOMAIN)
        exchange.is_complete = True
        exchange.response.blocked_by = key.name


    def process_question(self, exchange: Exchange):
        """

        Check whether the question rewrites to a Blackhole.
        Otherwise, add the rewrite to the currest response.

        """
        key_in = KeyDNS.from_exchange(exchange)
        key_out: KeyDNS = self.rewriter.get(key_in)

        if key_out == BLACKHOLE:
            # TODO: Not ideal. First we waste time comparing against the blocklist, and we also lose any rewrites that happened before the blackhole.
            # To fix properly, we'd probably need two separate transformers, one for rewrites, one of blocks.
            # It also means we need to clear cache to toggle blocking. We can add the blocking boolean to the cache key.
            self.block(exchange, key_in)
            if exchange.is_complete:
                return
            key_out = key_in

        if key_in is not key_out:  # TODO: Add whole rewrite chain as RRSets
            rrset = key_out.to_rrset(exchange.request.name)
            exchange.answers_pre.append(rrset)

        return

    def process_upstream(self, exchange: Exchange):
        """

        This is a bit awkward as we'd ideally transform each upstream answer.
        That would break the chain though, so we can't.
        Instead, just check whether any answer transforms to a Blackhole, blocking if so.

        """

        logger.info(f'Examining answer chain...')
        for rrset in exchange.response.message.answer:
            key = KeyDNS.from_rrset(rrset)
            output = self.rewriter.get(key)
            if output == BLACKHOLE:
                self.block(exchange, key)
                if exchange.is_complete:
                    return

        return

    def finalize(self, exchange: Exchange):
        """

        If we have additional answers to prepend to the exchange (e.g. from rewrites) then add them.

        """

        exchange.response.message.answer = exchange.answers_pre + exchange.response.message.answer
        exchange.response.message.question = exchange.request.message.question
        super().finalize(exchange)


if __name__ == '__main__':
    ...
