# Quick Start

## Create a settings file

Download or copy [`settings.example.yaml`](settings.example.yaml) into your
working directory as `settings.yaml`. At minimum, check the server address and
replace the example local resolver addresses with resolvers reachable from your
network.

## Run

Install `hold` into an environment with Python 3.14 or newer:

```console
pip install hold
hold --config ./settings.yaml
```

With `uv`, installation and launch can be a single command:

```console
uv run --with hold hold --config ./settings.yaml
```

`hold` listens for DNS queries on `server.host` and `server.port`. DNS uses port
53 by default, which normally requires additional privileges. See
[Running on port 53](settings.md#running-on-port-53), or override the configured
port for an initial test. The `--server` value is merged over the YAML settings:

```console
hold --config ./settings.yaml --server '{"port":5353}'
```

Query it with `dig`:

```console
dig @127.0.0.1 -p 5353 api.service A
```

Once the configuration works, point a router, local DNS forwarder, or selected
clients at `hold`. Binding directly to port 53 and installing `hold` as a service are
host-specific deployment tasks.

## Next steps

- Read [Settings](settings.md) to configure blocking and upstream resolvers.
- Read [Rewrite Rules](rewrite-rules.md) to build recursive name mappings and
  split-DNS routing.
