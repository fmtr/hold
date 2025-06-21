import dns as dnspython
import regex as re
from dataclasses import dataclass
from dns.rrset import RRset
from functools import cached_property
from typing import Self, List

from fmtr.dns import caching
from fmtr.dns.blocklist import BlockList
from fmtr.dns.obs import logger
from fmtr.dns.patterns import SUBDOMAINS
from fmtr.tools import dns
from fmtr.tools.dns_tools.client import Plain
from fmtr.tools.pattern_tools import Transformer, Key, Item, alt

client = dns.client

Request, Response, Exchange = dns.dm.Request, dns.dm.Response, dns.dm.Exchange


BLACKHOLE = 'BLACKHOLE'
ANSWER_PRE_TTL = 24 * 60 * 60


@dataclass
class KeyDNS(Key):
    """

    Key for transforming an RRSet using a set of rules

    """
    name: str
    records: str

    @classmethod
    def from_rrset(cls, rrset: RRset) -> Self:
        """

        From RRSet

        """
        records = rrset.rdtype.to_text(rrset.rdtype)
        self = cls(name=rrset.name.to_text(), records=records)
        return self

    @classmethod
    def from_exchange(cls, exchange: Exchange) -> Self:
        rrset = exchange.question_last
        self = cls.from_rrset(rrset)
        return self

    def to_rrset(self, name) -> RRset:
        """

        Create an RRSet mapping a source name to this key's name via this key's record.

        """
        rrset = dnspython.rrset.from_text(
            name,
            ANSWER_PRE_TTL,
            dnspython.rdataclass.IN,
            self.records,
            self.name,
        )

        return rrset


@dataclass
class RuleDNS(Item):
    source: KeyDNS
    target: KeyDNS | str


@dataclass
class RuleUpstream(RuleDNS):
    source: KeyDNS
    target: Plain


@dataclass
class TransformerDNS(Transformer):
    items: List[RuleDNS]
    blocklist: BlockList

    def __post_init__(self):
        """

        Add blocklist rule

        """

        domains = self.blocklist.refresh()

        patterns = [re.escape(domain) for domain in domains]
        pattern = alt(*patterns)
        pattern = f'{SUBDOMAINS}{pattern}'

        key = KeyDNS(
            name=pattern,
            records='AAAA|CNAME|A'
        )

        rule = RuleDNS(
            source=key,
            target=BLACKHOLE,
        )

        self.items.append(rule)

        super().__post_init__()

@dataclass
class Upstreams(Transformer):
    items: List[RuleUpstream]
    default: client.HTTP

    def resolve(self, exchange: Exchange):
        """

        Select the appropriate upstream resolver based on the question plus rules

        """

        key = KeyDNS.from_exchange(exchange)
        upstream = self.get(key)
        return upstream.resolve(exchange)


@dataclass(kw_only=True, eq=False)
class AdBlockDoHProxy(dns.proxy.Proxy):
    rewriter: TransformerDNS
    client: Upstreams | client.HTTP
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
        exchange.response.message.set_rcode(dnspython.rcode.NXDOMAIN)
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
