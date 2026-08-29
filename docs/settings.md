# Settings

`hold` reads YAML configuration from the path passed with `--config`. Using an
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

`hold` also accepts settings through command-line arguments and environment
variables. Nested environment keys use `__` and the package prefix is `HOLD__`;
for example, `HOLD__SERVER__PORT=5353`. YAML is recommended for rule sets because
the nested structures remain readable.

Command-line values take precedence over the settings file. Complex sections
such as `server` are passed as JSON and merged with their YAML values, so you can
temporarily change only the DNS port:

```console
hold --config ./settings.yaml --server '{"port":5353}'
```

## Blocklists

`hold` supports DNS Response Policy Zone (RPZ) blocklists served over HTTP or
HTTPS. Each usable line must contain exactly three whitespace-separated fields,
such as:

```text
ads.example CNAME .
```

The first field is treated as the blocked domain. Queries for that domain or any
of its subdomains are blocked for `A`, `AAAA`, and `CNAME` records. Plain
one-domain-per-line lists, hosts files, and Adblock Plus filter syntax are not
currently supported.

### How upstream answers are checked

Blocking is not limited to the name in the original question. After an upstream
resolver replies, `hold` examines every record set in the response's answer
chain. If any individual answer matches the blocklist—or is recursively rewritten
to `BLACKHOLE`—`hold` blocks the whole response and returns `NXDOMAIN`.

For example, a query for an otherwise acceptable name might reveal a blocked
tracker later in its CNAME chain:

```text
news.example.  CNAME  metrics.vendor.example.
metrics.vendor.example.  A  192.0.2.10
```

If `metrics.vendor.example` is blocked, the second answer causes the complete
response to be blocked. This prevents an allowed alias from being used to reach
a blocked destination indirectly.

The example uses the small [OISD](https://oisd.nl/) RPZ list:

```yaml
blocklist:
  url: https://small.oisd.nl/rpz
  limit: 100
```

OISD also publishes a larger list at `https://big.oisd.nl/rpz`; its website
describes the available variants and policies. Set `limit: 0` to load the entire
selected list. Downloads are cached on disk, loaded at startup, and can be
forcibly re-downloaded through the HTTP control API. Start with a small limit while
checking memory use, lookup behaviour, and false positives on your network.

## Running on port 53

The example uses the standard DNS port, 53. Linux normally prevents unprivileged
processes from opening ports below 1024. You can lower the kernel's unprivileged
port boundary to 53 until the next reboot:

```console
sudo sysctl -w net.ipv4.ip_unprivileged_port_start=53
```

This is a system-wide change: unprivileged processes will be able to bind any
otherwise-available port from 53 upward. If that trade-off is unsuitable, grant
the service a narrowly scoped bind capability through your service manager.
Running `sudo hold ...` is also possible, but running the entire DNS service as
root is not recommended.

The HTTP control API is launched alongside DNS and provides endpoints to clear
the response cache, refresh the blocklist, and toggle blocking. Treat it as a
local administration interface and do not expose it to an untrusted network.
