import dns
import pytest

from corio.dns.dm import Exchange
from fmtr.dns.proxy import AdBlockDoHProxy
from fmtr.dns.transformer import KeyDNS


def make_exchange(name="hello.test.", record_type="A"):
    query = dns.message.make_query(name, record_type)
    return Exchange.from_wire(query.to_wire(), ip="127.0.0.1", port=5353)


@pytest.mark.asyncio
async def test_address_rewrite_is_final_and_skips_upstream():
    class Rewriter:
        def get(self, key):
            return KeyDNS(name="1.2.3.4", records="A")

    class Upstream:
        called = False

        async def resolve(self, exchange):
            self.called = True

    upstream = Upstream()
    proxy = AdBlockDoHProxy(
        host="127.0.0.1",
        port=5353,
        rewriter=Rewriter(),
        client=upstream,
    )
    exchange = make_exchange()

    await proxy.resolve(exchange)

    assert exchange.is_complete
    assert not upstream.called
    assert exchange.response.rcode == dns.rcode.NOERROR
    assert exchange.response.answer.to_text().endswith("A 1.2.3.4")


@pytest.mark.asyncio
async def test_cname_rewrite_continues_upstream():
    class Rewriter:
        def get(self, key):
            if key.name == "hello.test.":
                return KeyDNS(name="target.lan.", records="CNAME")
            return key

    class Upstream:
        called = False

        async def resolve(self, exchange):
            self.called = True
            response = exchange.request.get_response_template()
            response.answer.append(
                dns.rrset.from_text("target.lan.", 60, "IN", "A", "1.2.3.4")
            )
            exchange.response = exchange.response.from_message(response)

    upstream = Upstream()
    proxy = AdBlockDoHProxy(
        host="127.0.0.1",
        port=5353,
        rewriter=Rewriter(),
        client=upstream,
    )
    exchange = make_exchange()

    await proxy.resolve(exchange)

    assert upstream.called
    assert exchange.is_complete
    assert [answer.rdtype for answer in exchange.response.message.answer] == [
        dns.rdatatype.CNAME,
        dns.rdatatype.A,
    ]
