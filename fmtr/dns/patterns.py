DOMAIN_CHARS = r'a-zA-Z0-9-'

FILLS = dict(
    SUBDOMAIN=fr'[{DOMAIN_CHARS}]+',
    SUBDOMAINS=fr'[{DOMAIN_CHARS}\.]+'
)
