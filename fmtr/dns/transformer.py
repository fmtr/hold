from dataclasses import dataclass
from typing import Self, List

from fmtr import tools
from fmtr.dns import patterns
from fmtr.dns.blocklist import BlockList
from fmtr.dns.constants import BLACKHOLE, ANSWER_PRE_TTL, SUBDOMAINS
from fmtr.tools import dns
from fmtr.tools.dns_tools.client import Plain


@dataclass
class KeyDNS(tools.patterns.Key):
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
class RuleDNS(tools.patterns.Item):
    source: KeyDNS
    target: KeyDNS | str


@dataclass
class RuleUpstream(RuleDNS):
    source: KeyDNS
    target: Plain


@dataclass
class TransformerDNS(tools.patterns.Transformer):
    items: List[RuleDNS]
    blocklist: BlockList

    def __post_init__(self):
        """

        Add blocklist rule

        """

        domains = self.blocklist.refresh()

        patterns = [tools.patterns.re.escape(domain) for domain in domains]
        pattern = tools.patterns.alt(*patterns)
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
