from fmtr.dns.server import AdBlockDoHProxy
from fmtr.tools import sets
from fmtr.tools.pattern_tools import Rewrite, Transformer


class Settings(sets.Base):
    paths = sets.PackagePaths()

    server: AdBlockDoHProxy
    rw: Transformer


settings = Settings()
settings
