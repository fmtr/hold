from fmtr.dns.paths import paths
from fmtr.dns.proxy import AdBlockDoHProxy
from fmtr.tools import sets


class Settings(sets.Base):
    paths = paths
    server: AdBlockDoHProxy
