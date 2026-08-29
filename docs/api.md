# Control API

`hold` launches a small HTTP control API alongside the DNS server. It provides
the following `POST` endpoints:

| Endpoint | Action |
| --- | --- |
| `/cache/clear` | Clear cached DNS responses. |
| `/blocking/refresh` | Discard the cached download, fetch the blocklist again, and clear cached DNS responses. |
| `/blocking/toggle` | Enable or disable blocking and clear cached DNS responses. |

The API is intended for local administration and has no built-in authentication
or authorization. Do not expose it directly to an untrusted network. If remote
access is required, put it behind a suitably configured reverse proxy that adds
authentication, access control, and transport security.
