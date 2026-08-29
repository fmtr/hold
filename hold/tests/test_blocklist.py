from corio.caching import Disk
from hold.blocklist import BlockList
from hold.constants import BLACKHOLE
from hold.transformer import KeyDNS, RuleDNS, TransformerDNS


def test_blocklist_cache_key_includes_url_and_limit(tmp_path):
    blocklist = BlockList(url="https://big.oisd.nl/rpz")
    disk = Disk(tmp_path)
    blocklist.disk = disk

    key = blocklist.download.__cache_key__(
        blocklist.url,
        blocklist.limit,
    )
    assert "https://big.oisd.nl/rpz" in repr(key)
    assert 0 in key

    disk[key] = ["cached.example."]
    assert blocklist.refresh() == frozenset({"cached.example."})


def test_blocklist_cache_keys_differ_by_configuration(tmp_path):
    disk = Disk(tmp_path)
    blocklists = [
        BlockList(url="https://small.oisd.nl/rpz", limit=0),
        BlockList(url="https://big.oisd.nl/rpz", limit=0),
        BlockList(url="https://big.oisd.nl/rpz", limit=100),
    ]

    for blocklist in blocklists:
        blocklist.disk = disk

    keys = {
        blocklist.download.__cache_key__(
            blocklist.url,
            blocklist.limit,
        )
        for blocklist in blocklists
    }
    assert len(keys) == len(blocklists)


def test_blocklist_matches_domains_and_subdomains():
    blocklist = BlockList(url="unused")
    blocklist.domains = frozenset({"blocked.example."})

    assert blocklist.get(KeyDNS(name="blocked.example.", records="A")) == BLACKHOLE
    assert blocklist.get(KeyDNS(name="a.b.blocked.example.", records="AAAA")) == BLACKHOLE
    assert blocklist.get(KeyDNS(name="BLOCKED.EXAMPLE.", records="CNAME")) == BLACKHOLE


def test_blocklist_returns_original_key_for_non_matches():
    blocklist = BlockList(url="unused")
    blocklist.domains = frozenset({"blocked.example."})
    allowed = KeyDNS(name="allowed.example.", records="A")
    unsupported = KeyDNS(name="blocked.example.", records="MX")

    assert blocklist.get(allowed) is allowed
    assert blocklist.get(unsupported) is unsupported


def test_refresh_atomically_replaces_domain_set():
    blocklist = BlockList(url="unused")
    blocklist.domains = frozenset({"old.example."})
    blocklist.download = lambda url, limit: ["NEW.EXAMPLE.", "new.example."]

    domains = blocklist.refresh()

    assert domains == frozenset({"new.example."})
    assert blocklist.domains is domains


def test_recursive_transform_checks_rewritten_names_against_blocklist():
    blocklist = BlockList(url="unused")
    blocklist.domains = frozenset({"blocked.example."})
    transformer = TransformerDNS(
        items=[
            RuleDNS(
                source=KeyDNS(name=r"alias\.example\.", records="A"),
                target=KeyDNS(name="blocked.example.", records="CNAME"),
            ),
        ],
        blocklist=blocklist,
        is_recursive=True,
    )

    result = transformer.get(KeyDNS(name="alias.example.", records="A"))

    assert result == BLACKHOLE


def test_refresh_replaces_blocklist_without_recompiling_transformer():
    blocklist = BlockList(url="unused")
    blocklist.download = lambda url, limit: ["blocked.example."]
    transformer = TransformerDNS(items=[], blocklist=blocklist)

    def fail_compile(*args, **kwargs):
        raise AssertionError("transformer should not be recompiled")

    transformer.compile = fail_compile

    count = transformer.refresh_blocklist()

    assert count == 1
    assert blocklist.domains == frozenset({"blocked.example."})
