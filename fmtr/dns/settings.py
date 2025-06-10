from fmtr.dns.server import AdBlockDoHProxy
from fmtr.tools import sets


class Settings(sets.Base):
    paths = sets.PackagePaths()
    server: AdBlockDoHProxy
