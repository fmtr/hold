from dataclasses import dataclass

from corio import caching, https
from fmtr.dns.obs import logger


@dataclass(frozen=True)
class BlockList:
    SPECIALS = ('$', '@', '*', ' ', ';', 'NS')

    url: str
    limit: int = 0

    def bind_disk(self, disk: caching.Disk):
        object.__setattr__(self, 'disk', disk)
        object.__setattr__(self, 'refresh', disk.memoize()(self._refresh))

    @logger.instrument('Clearing cache...')
    def reset(self):
        key = self.refresh.__cache_key__()
        if key in self.disk:
            del self.disk[key]

    @logger.instrument('Refreshing blocklist...')
    def _refresh(self):
        response = https.client.get(self.url)
        response.raise_for_status()
        text = response.text

        domains = self.get_domains(text)
        return domains

    @logger.instrument('Extracting domains...')
    def get_domains(self, text):
        domains = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue

            if any(line.startswith(special) for special in self.SPECIALS):
                continue

            domain, _, _ = line.split()
            domain = f'{domain}.'
            domains.append(domain)

            if self.limit and len(domains) == self.limit:
                break

        logger.info(f'{len(domains)=} {self.limit=}')

        return domains


if __name__ == '__main__':
    bl = BlockList(url='https://small.oisd.nl/rpz')
    bl.bind_disk(caching.Disk('/tmp/blocklist-cache'))
    doms = bl.refresh()
    bl.reset()
    doms
