import dns as dnspython
import regex as re
from dataclasses import dataclass
from dns.rrset import RRset
from typing import Self, List

from fmtr.dns.blocklist import BlockList
from fmtr.dns.obs import logger
from fmtr.dns.patterns import SUBDOMAINS
from fmtr.tools import dns
from fmtr.tools.dns_tools.client import Plain
from fmtr.tools.pattern_tools import Transformer, Key, Item, alt

client = dns.client

Request, Response, Exchange = dns.dm.Request, dns.dm.Response, dns.dm.Exchange


BLACKHOLE = 'BLACKHOLE'


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
            300,  # TODO: What should this be?
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


    def block(self, exchange: Exchange):
        """

        Remove any existing answers, set NXDOMAIN and complete

        """
        exchange.response.message.answer.clear()
        exchange.response.message.set_rcode(dnspython.rcode.NXDOMAIN)
        exchange.response.is_complete = True
        logger.warning(f'Request blocked.')

    def process_question(self, exchange: Exchange):
        """

        Check whether the question rewrites to a Blackhole.
        Otherwise, add the rewrite to the currest response.

        """

        key = KeyDNS.from_exchange(exchange)
        output: KeyDNS = self.rewriter.get(key)

        if output == BLACKHOLE:
            return self.block(exchange)

        if key is not output:  # TODO: Add whole rewrite chain as RRSets
            rrset = output.to_rrset(exchange.request.name)
            exchange.response.message.answer.append(rrset)

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
                return self.block(exchange)

        return


if __name__ == '__main__':
    ...
