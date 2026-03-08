from dataclasses import dataclass

from corio import http
from fmtr.dns.caching import disk
from fmtr.dns.obs import logger


@dataclass(frozen=True)
class BlockList:
    SPECIALS = ('$', '@', '*', ' ', ';', 'NS')

    url: str
    limit: int = 0

    @logger.instrument('Clearing cache...')
    def reset(self):
        key = self.refresh.__cache_key__(self)
        if key in disk:
            del disk[key]

    @disk.memoize()
    @logger.instrument('Refreshing blocklist...')
    def refresh(self):
        """


        """
        response = http.client.get(self.url)
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
    doms = bl.refresh()
    bl.reset()
    doms
