from dataclasses import dataclass, field
from functools import cached_property
from httpx_retries import Retry

from corio import caching, https
from hold.constants import BLACKHOLE
from hold.obs import logger


class HTTPClientBlocklist(https.Client):
    TIMEOUT = 5

    @cached_property
    def retry(self):
        return Retry(
            total=1,
            allowed_methods={'GET'},
            backoff_factor=0.25,
            max_backoff_wait=1,
            respect_retry_after_header=False,
        )


@dataclass
class BlockList:
    SPECIALS = ('$', '@', '*', ' ', ';', 'NS')
    CLIENT = HTTPClientBlocklist()
    RECORDS = frozenset({'A', 'AAAA', 'CNAME'})

    url: str
    limit: int = 0
    target: str = BLACKHOLE
    disk: caching.Disk = field(init=False, repr=False, compare=False)
    domains: frozenset[str] = field(
        init=False,
        default_factory=frozenset,
        repr=False,
        compare=False,
    )

    @cached_property
    def download(self):
        @self.disk.memoize()
        @logger.instrument('Downloading blocklist...')
        def download(url: str, limit: int):
            response = self.CLIENT.get(url)
            response.raise_for_status()
            return self.get_domains(response.text, limit)

        return download

    @logger.instrument('Extracting domains...')
    def get_domains(self, text: str, limit: int):
        domains = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue

            if any(line.startswith(special) for special in self.SPECIALS):
                continue

            domain, _, _ = line.split()
            domains.append(f'{domain}.')

            if limit and len(domains) == limit:
                break

        logger.info(f'{len(domains)=} {limit=}')
        return domains

    @logger.instrument('Refreshing blocklist...')
    def refresh(self):
        domains = self.download(self.url, self.limit)
        self.domains = frozenset(domain.lower() for domain in domains)
        return self.domains

    def matches(self, key) -> bool:
        if key.records not in self.RECORDS:
            return False

        name = key.name.lower()
        if name in self.domains:
            return True

        return any(
            name[index + 1:] in self.domains
            for index, character in enumerate(name)
            if character == '.' and index + 1 < len(name)
        )

    def get(self, key):
        if self.matches(key):
            return self.target

        return key

    @logger.instrument('Clearing cache...')
    def reset(self):
        key = self.download.__cache_key__(self.url, self.limit)
        if key in self.disk:
            del self.disk[key]


if __name__ == '__main__':
    bl = BlockList(url='https://small.oisd.nl/rpz')
    from corio import caching
    bl.disk = caching.Disk('/tmp/blocklist-cache')
    doms = bl.refresh()
    bl.reset()
    doms
