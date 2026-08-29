# Recursive Rewrite Rules

`hold` treats a DNS question as a pair: its fully qualified name and requested
record type. Each rule has a source pattern for that pair and either a new pair
or the special target `BLACKHOLE`.

In simplified pseudo-code, a single pass looks like this:

```text
for rule in rules:
    if rule.source fully matches (name, record_type):
        captures = values matched by placeholders
        return fill(rule.target, captures)
return input
```

With `is_recursive: true`, `hold` feeds each result back into the same transformer
until no rule changes it:

```text
value = question
repeat:
    next = rewrite_once(value)
    if next == value: return value
    if next was already seen: raise circular-loop error
    value = next
```

This turns a collection of small, composable rules into a transformation graph.
You can normalize a convenient suffix first, map the normalized name to an
address second, and still have the final result checked against the blocklist.

## Captures and substitutions

`{SUBDOMAIN}` matches and captures one DNS label. `{SUBDOMAINS}` matches a dotted
sequence. A placeholder used in a target is replaced with the text captured by
the source rule:

```text
{SUBDOMAIN}\.service\.  =>  {SUBDOMAIN}.lan.
api.service.            =>  api.lan.
```

The other source fields are regular expressions too. For example,
`A|AAAA|CNAME` allows a rule to apply to three record types. Patterns are full
matches, literal dots need escaping, and names include the trailing root dot.

## Transformation examples

```text
# Preserve a service label, then resolve every local service to one host.
{name}.service. -> {name}.lan. -> 192.168.1.10

# Normalize an overlay suffix, then select its private resolver.
{name}.vpn. -> {name}.example.net. -> resolver 100.100.100.100

# Block directly or after another rewrite reaches the blocked name.
ads.example. -> BLACKHOLE
tracking.short. -> ads.example. -> BLACKHOLE
```

The corresponding abbreviated YAML is:

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

Rule order matters when source patterns overlap. Prefer narrow patterns and test
each chain independently. Circular rewrite chains are detected and rejected,
rather than being followed forever.

## Upstream routing

The `client.items` list uses the same pattern machinery to select a DNS resolver.
This keeps routing rules beside rewrite rules: public names can go to the default
DNS-over-HTTPS service, while `.lan`, VPN, and reverse-DNS names go directly to
the resolver authoritative for that network. See the [example settings](settings.md).
