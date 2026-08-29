# Quick Start

## Create a settings file

Download or copy [`settings.example.yaml`](settings.example.yaml) into your
working directory as `settings.yaml`. At minimum, check the server address and
replace the example local resolver addresses with resolvers reachable from your
network.

## Run

Install Hold into an environment with Python 3.14 or newer:

```console
pip install hold
hold --config ./settings.yaml
```

With `uv`, installation and launch can be a single command:

```console
uv run --with hold hold --config ./settings.yaml
```

Hold listens for DNS queries on `server.host` and `server.port`. Port 53 usually
requires elevated privileges, so the example uses port 5354 for initial testing.

Query it with `dig`:

```console
dig @127.0.0.1 -p 5354 api.service A
```

Once the configuration works, point a router, local DNS forwarder, or selected
clients at Hold. Binding directly to port 53 and installing Hold as a service are
host-specific deployment tasks.

## Next steps

- Read [Settings](settings.md) to configure blocking and upstream resolvers.
- Read [Rewrite Rules](rewrite-rules.md) to build recursive name mappings and
  split-DNS routing.
