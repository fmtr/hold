import asyncio
import threading
from types import SimpleNamespace

import pytest

from hold.api import DNS, RefreshBlocklist


@pytest.mark.asyncio
async def test_refresh_blocklist_runs_off_event_loop_and_fetches_once():
    release_refresh = threading.Event()
    released_by_event_loop = False
    refresh_calls = 0
    clear_values = []

    class Rewriter:
        def refresh_blocklist(self, *, clear=False):
            nonlocal released_by_event_loop, refresh_calls
            refresh_calls += 1
            clear_values.append(clear)
            released_by_event_loop = release_refresh.wait(timeout=0.5)
            return 17

        blocklist = SimpleNamespace(refresh=lambda: [None] * 17)

    class Cache:
        cleared = False

        def clear(self):
            self.cleared = True

    cache = Cache()
    server = SimpleNamespace(rewriter=Rewriter(), cache=cache)
    endpoint = RefreshBlocklist(SimpleNamespace(dns_server=server))

    asyncio.get_running_loop().call_later(0.01, release_refresh.set)
    assert await endpoint.run() == 17
    assert released_by_event_loop
    assert refresh_calls == 1
    assert clear_values == [True]
    assert cache.cleared


@pytest.mark.asyncio
async def test_startup_blocklist_load_waits_until_dns_is_serving():
    dns_started = False
    refreshed_after_start = False

    class Rewriter:
        def refresh_blocklist(self):
            nonlocal refreshed_after_start
            refreshed_after_start = dns_started
            return 17

    class Server:
        rewriter = Rewriter()

        async def wait_started(self):
            nonlocal dns_started
            dns_started = True

    api = SimpleNamespace(dns_server=Server())
    assert await DNS.load_blocklist(api) == 17
    assert refreshed_after_start
