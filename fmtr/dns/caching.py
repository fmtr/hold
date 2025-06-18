from datetime import timedelta

from fmtr.dns.obs import logger
from fmtr.dns.paths import paths
from fmtr.tools import caching

disk = caching.Disk(paths.cache)


class CacheDNS(caching.TLRU):
    """

    Subclass to include logging and simplify global TTU

    """

    def get_ttu(self, key, response, now) -> float | timedelta:
        """

        Select the minimum TTL of all answers in the response

        """
        ttls = [answer.ttl for answer in response.message.answer] or {0}
        seconds = min(ttls)
        delta = timedelta(seconds=seconds)
        logger.debug(f'Setting cache TTL: {self.MASK_MAPPING.format(key=key, value=delta)}')
        ttu = now + delta
        return ttu
