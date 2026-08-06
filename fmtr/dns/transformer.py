import typing
from dataclasses import dataclass
from typing import Self, List

import corio
from corio import dns
from corio.dns.client import Plain
from fmtr.dns import patterns
from fmtr.dns.blocklist import BlockList
from fmtr.dns.constants import BLACKHOLE, ANSWER_PRE_TTL, SUBDOMAINS
from fmtr.dns.obs import logger


@dataclass
class KeyDNS(corio.patterns.Key):
    """

    Key for transforming an RRSet using a set of rules

    """
    FILLS = patterns.FILLS
    name: str
    records: str

    @classmethod
    def from_rrset(cls, rrset: dns.dns.rrset.RRset) -> Self:
        """

        From RRSet

        """
        records = rrset.rdtype.to_text(rrset.rdtype)
        self = cls(name=rrset.name.to_text(), records=records)
        return self

    @classmethod
    def from_exchange(cls, exchange: dns.dm.Exchange) -> Self:
        rrset = exchange.question_last
        self = cls.from_rrset(rrset)
        return self

    def to_rrset(self, name) -> dns.dns.rrset.RRset:
        """

        Create an RRSet mapping a source name to this key's name via this key's record.

        """
        rrset = dns.dns.rrset.from_text(
            name,
            ANSWER_PRE_TTL,
            dns.dns.rdataclass.IN,
            self.records,
            self.name,
        )

        return rrset


@dataclass
class RuleDNS(corio.patterns.Item):
    source: KeyDNS
    target: KeyDNS | str


@dataclass
class RuleBlocklistDNS(RuleDNS):
    ...


@dataclass
class RuleUpstream(RuleDNS):
    source: KeyDNS
    target: Plain


@dataclass
class TransformerDNS(corio.patterns.Transformer):
    items: List[RuleDNS]
    blocklist: BlockList

    def __post_init__(self):
        super().__post_init__()

    def refresh_blocklist(self, *, clear=False):
        if clear:
            self.blocklist.reset()
        domains = self.add_blocklist()
        self.compile(clear=True)
        return len(domains)

    def add_blocklist(self):

        try:
            domains = self.blocklist.refresh()
        except Exception as exception:
            logger.error(f'Error refreshing blocklist. Skipping to allow start-up: {repr(exception)}')
            return []

        logger.info(f'Blocklist loaded: {len(domains)=}')

        patterns = [corio.patterns.re.escape(domain) for domain in domains]
        pattern = corio.patterns.alt(*patterns)
        pattern = f'{SUBDOMAINS}{pattern}'

        key = KeyDNS(
            name=pattern,
            records='AAAA|CNAME|A'
        )

        rule = RuleBlocklistDNS(
            source=key,
            target=BLACKHOLE,
        )

        self.items = [item for item in self.items if type(item) is not RuleBlocklistDNS]  # Bit goofy, but only way to pop out just the blocklist rule.
        self.items.append(rule)
        return domains
