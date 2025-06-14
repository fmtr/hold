from fmtr.dns.paths import paths
from fmtr.dns.server import AdBlockDoHProxy
from fmtr.tools import sets


class Settings(sets.Base):
    paths = paths
    server: AdBlockDoHProxy
