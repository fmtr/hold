# Blocking

`hold` can block names explicitly with rewrite rules or from a downloaded
blocklist. A blocked query receives an `NXDOMAIN` response.

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

The example settings use the small [OISD](https://oisd.nl/) RPZ list:

```yaml
blocklist:
  url: https://small.oisd.nl/rpz
  limit: 100
```

OISD also publishes a larger list at `https://big.oisd.nl/rpz`; its website
describes the available variants and policies. Set `limit: 0` to load the entire
selected list. Downloads are cached on disk and loaded at startup. Start with a
small limit while checking memory use, lookup behaviour, and false positives on
your network.

## How upstream answers are checked

Blocking is not limited to the name in the original question. After an upstream
resolver replies, `hold` examines every record set in the response's answer
chain. If any individual answer matches the blocklist—or is recursively
rewritten to `BLACKHOLE`—`hold` blocks the whole response and returns `NXDOMAIN`.

For example, both the requested name and final host might be acceptable while a
blocked tracker appears only in the middle of the CNAME chain:

```text
news.example.             CNAME  tracker.bad.example.
tracker.bad.example.      CNAME  content.cdn.example.
content.cdn.example.      A      192.0.2.10
```

If `tracker.bad.example` is blocked, the middle answer causes the complete
response to be blocked. A naive check of only `news.example` or the terminal
`content.cdn.example` answer would miss it.

## Explicit blocking rules

The special rewrite target `BLACKHOLE` blocks a name without adding it to the
downloaded list:

```yaml
- source:
    name: 'ads\.example\.'
    records: 'A|AAAA|CNAME'
  target: BLACKHOLE
```

Because rewrites can be recursive, a name is also blocked if a sequence of
rewrite rules eventually produces `BLACKHOLE`. See [Rewrite Rules](rewrite-rules.md)
for details.
