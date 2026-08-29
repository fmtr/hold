# `hold`

`hold` is a small, ad-blocking DNS server for home labs. It forwards ordinary
queries to DNS-over-HTTPS or local DNS resolvers, caches responses, and exposes
a small HTTP API for clearing the cache, refreshing the blocklist, and toggling
blocking.

The distinctive part is its rule-driven transformer. Rules match both DNS names
and record types, capture reusable parts of a name, and construct a new DNS
answer from those captures. Rewrites can be recursive, so the output of one rule
can become the input to another:

```text
api.service.  --rewrite-->  api.lan.  --rewrite-->  192.168.1.10
printer.vpn.  --rewrite-->  printer.example.net.  --route-->  private DNS
ads.example.  --rewrite-->  BLACKHOLE
```

That makes `hold` useful when a home network has several naming schemes, split
DNS, overlay-network names, or local services that should resolve without
maintaining every hostname individually.

## Should I use this instead of Pi-hole or AdGuard Home?

Probably not if you mainly want a polished DNS appliance. Pi-hole and AdGuard
Home are considerably more mature, have friendly administration interfaces, and
are better choices for most networks.

`hold` exists for cases where their record-rewrite systems are too limited. A
single `hold` rule can map `{domain}.service.` to `{domain}.lan.`, retain the
captured label, pass the result through further rules, and choose a resolver from
the transformed name. Blocking participates in the same recursive pipeline, so
a rewrite that eventually reaches a blocked domain is blocked too.

## Install and run

`hold` requires Python 3.14 or newer. Install it from PyPI:

```console
pip install hold
hold --config ./settings.yaml
```

Or run it without a permanent installation using
[uv](https://docs.astral.sh/uv/):

```console
uv run --with hold hold --config ./settings.yaml
```

Copy [the example settings file](docs/settings.example.yaml), adjust the listen
address and upstream resolvers for your network, then point a test client at the
configured port. `hold` is intended for trusted home-lab networks, not exposed or
high-availability production infrastructure.

DNS normally uses port 53, which most operating systems reserve for privileged
processes. On Linux, you can allow unprivileged processes to bind from port 53
upward until the next reboot with:

```console
sudo sysctl -w net.ipv4.ip_unprivileged_port_start=53
```

Running `hold` with `sudo` also works, but running the whole service as root is
not recommended. For an initial test, leave the settings file unchanged and
override its port from the command line:

```console
hold --config ./settings.yaml --server '{"port":5353}'
```

## Rewrite rules at a glance

Sources are regular-expression patterns. `{SUBDOMAIN}` captures one label and
`{SUBDOMAINS}` captures one or more labels; captured values can be inserted into
the target:

```yaml
rewriter:
  is_recursive: true
  items:
    - source: {name: '{SUBDOMAIN}\.service\.', records: 'A|AAAA|CNAME'}
      target: {name: '{SUBDOMAIN}.lan.', records: CNAME}
    - source: {name: '{SUBDOMAIN}\.lan\.', records: 'A|AAAA|CNAME'}
      target: {name: 192.168.1.10, records: A}
    - source: {name: 'ads\.example\.', records: 'A|AAAA|CNAME'}
      target: BLACKHOLE
```

See the [rewrite guide](docs/rewrite-rules.md) for matching, recursion, routing,
and a larger example. See the [quick start](docs/quick-start.md) and
[settings reference](docs/settings.md) for operation.

## Documentation

- Published documentation: https://fmtr.github.io/hold
- Documentation source: [docs](docs)

## License

`hold` is licensed under Apache 2.0.
