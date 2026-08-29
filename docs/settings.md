# Settings

Hold reads YAML configuration from the path passed with `--config`. Using an
explicit path makes service deployments predictable:

```console
hold --config /etc/hold/settings.yaml
```

The complete starter configuration is embedded below.

```yaml
--8<--
docs/settings.example.yaml
--8<--
```

## Main sections

- `server.host` and `server.port` select the DNS listening address.
- `server.rewriter` contains the ordered rewrite rules and the downloaded
  blocklist. Set `limit` to `0` to load the whole list; a small value is useful
  while testing.
- `server.client.default` is the default DNS-over-HTTPS resolver.
- `server.client.items` routes matching queries to different resolvers. This is
  useful for local zones, VPN names, and reverse DNS.
- Top-level `cache` optionally changes the directory used for the downloaded
  blocklist cache.

Rules and upstreams are selected by full regular-expression matches, so literal
dots must be escaped as `\.`. DNS names are represented with their final dot.

Hold also accepts settings through command-line arguments and environment
variables. Nested environment keys use `__` and the package prefix is `HOLD__`;
for example, `HOLD__SERVER__PORT=5354`. YAML is recommended for rule sets because
the nested structures remain readable.

The HTTP control API is launched alongside DNS and provides endpoints to clear
the response cache, refresh the blocklist, and toggle blocking. Treat it as a
local administration interface and do not expose it to an untrusted network.
