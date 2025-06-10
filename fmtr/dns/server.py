from dataclasses import dataclass
from typing import Self

import dns as dnspython
from dns import rdatatype
from dns.rrset import RRset

from fmtr.tools import logger, dns
from fmtr.tools.dns_tools.client import Plain
from fmtr.tools.pattern_tools import Transformer, Key, Item

Request, Response, Exchange = dns.dm.Request, dns.dm.Response, dns.dm.Exchange

BLACKHOLE = 'BLACKHOLE'


@dataclass
class Upstreams(Transformer):

    def resolve(self, exchange: Exchange):
        """

        Select the appropriate upstream resolver based on the question plus rules

        """

        key = KeyDNS.from_exchange(exchange)
        upstream = self.get(key)
        return upstream.resolve(exchange)


@dataclass
class AdBlockDoHProxy(dns.proxy.Proxy):
    rewriter: Transformer

    def block(self, exchange: Exchange):
        """

        Remove any existing answers and set NXDOMAIN and complete

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
        rrset = dnspython.rrset.from_text(
            name,
            300,
            dnspython.rdataclass.IN,
            self.records,
            self.name,
        )

        return rrset


if __name__ == '__main__':
    data = {

        r'(?P<subd>[a-zA-Z]+)\.vpn.': '{subd}.barbel-boa.ts.net',
        r'(?P<subd>[a-zA-Z]+)\.go.': '{subd}.google.com',
        r'(?P<name>[a-z]+)\.dev\.example\.com': '{name}.test.example.com',
        r'img\d+\.static\.cdn\.example\.com': 'images.cdn.example.com',
        r'service\.(?P<env>dev|staging|prod)\.example\.org': '{env}-service.example.org',
        r'legacy\.(?P<region>[a-z]+)\.oldsite\.com': '{region}.newsitenow.com',
        r'shop\.(?P<country_code>[a-z]{2})\.example\.net': 'store.{country_code}.example.net',
        r'(?P<user>[a-z]+)\.mail\.example\.com': '{user}.email.example.com',
        r'app1\.cluster(?P<num>[0-9]+)\.example\.cloud': 'service{num}.example.cloud',
        r'(?P<project>[a-z]+)\.research\.corp\.com': '{project}.lab.corp.com',
        r'cdn\.(?P<version>v[0-9]+)\.content\.net': 'static.{version}.content.net',
        # Literal rule without named group
        r'corp\.secureaccess\.com': 'access.corp.com',
        # Literal rule without named group
        r'redirect\.oldsite\.org': 'homepage.newsite.org',
        # # Recursive rules

        r'archive\.(?P<year>\d{4})\.oldsite\.net': 'legacy.{year}.oldsite.net',  # Recursive matching
        r'legacy\.(?P<year>\d{4})\.oldsite\.net': 'archive-backup.{year}.net',  # Continuation

        # r'(?P<subd>[a-zA-Z]+)\.vpn': '{subd}.loop.ts.net',
        # r'(?P<subd>[a-zA-Z]+)\.loop\.ts\.net': '{subd}.vpn',  # Recursive loop back to .vpn

        r'bad\.test\.fmtr\.dev\.': 'spam.com.'
    }

    A_LIKES = (rdatatype.A, rdatatype.AAAA, rdatatype.CNAME)
    A_LIKES = [rdatatype.to_text(a) for a in A_LIKES]

    items = [
        Item(
            source=KeyDNS(
                records='AAAA|CNAME|A',
                name=r'(?P<subd>[a-zA-Z]+)\.vpn.',
            ),
            target=KeyDNS(
                records='CNAME',
                name='{subd}.barbel-boa.ts.net.',

            )
        ),

        Item(
            source=KeyDNS(
                records='AAAA|CNAME|A',
                name=r'(?P<subd>[a-zA-Z]+)\.test.',
            ),
            target=KeyDNS(
                records='A',
                name='1.2.3.4',

            )
        ),
        Item(
            source=KeyDNS(
                records='AAAA|CNAME|A',
                name=r'spam\.com\.',
            ),
            target=BLACKHOLE
        ),
        Item(
            source=KeyDNS(
                records='AAAA|CNAME|A',
                name=r'bad\.test\.fmtr\.dev\.',
            ),
            target=KeyDNS(
                records='CNAME',
                name='spam.com.',

            )
        ),
    ]

    ups_ts = Plain('100.100.100.100')
    ups_google = dns.client.HTTP(url='https://{host}/dns-query', host='dns.google')

    items_ups = [
        Item(
            source=KeyDNS(
                records='AAAA|CNAME|A',
                name=r'(?P<subd>[a-zA-Z]+)\.barbel-boa\.ts\.net\.',
            ),
            target=ups_ts,
        )
    ]

    rewriter = Transformer(items=items, is_recursive=True)
    ups = Upstreams(items=items_ups, is_recursive=False, default=ups_google)

    proxy = AdBlockDoHProxy("10.0.10.31", 5354, rewriter=rewriter, client=ups)
    proxy.start()
