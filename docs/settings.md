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
  blocklist. See [Blocking](blocking.md) for supported lists and matching
  behaviour.
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

The [Control API](api.md) is launched alongside DNS and provides endpoints to
clear the response cache, refresh the blocklist, and toggle blocking.
