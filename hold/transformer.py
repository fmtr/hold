from dataclasses import dataclass
from typing import Self, List

from corio import dns, patterns as patterns_corio
from corio.dns.client import Plain
from hold import patterns
from hold.blocklist import BlockList
from hold.constants import ANSWER_PRE_TTL
from hold.obs import logger


@dataclass
class KeyDNS(patterns_corio.Key):
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
class RuleDNS(patterns_corio.Item):
    source: KeyDNS
    target: KeyDNS | str


@dataclass
class RuleUpstream(RuleDNS):
    source: KeyDNS
    target: Plain


@dataclass
class TransformerDNS(patterns_corio.Transformer):
    items: List[RuleDNS]
    blocklist: BlockList

    def __post_init__(self):
        super().__post_init__()

    def refresh_blocklist(self, *, clear=False):
        if clear:
            self.blocklist.reset()

        try:
            domains = self.blocklist.refresh()
        except Exception as exception:
            logger.error(f'Error refreshing blocklist. Skipping to allow start-up: {repr(exception)}')
            return 0

        logger.info(f'Blocklist loaded: {len(domains)=}')
        return len(domains)

    def get_one(self, key: KeyDNS):
        value = self.blocklist.get(key)
        if value is not key:
            return value

        return super().get_one(key)
