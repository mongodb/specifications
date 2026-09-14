# Public Suffix List tests

These tests verify that a driver determines the public suffix of a domain correctly, as described in
[Determining the public suffix](../public-suffix-list.md#determining-the-public-suffix).

## Prose Tests

Each test below states the case being covered, then the public suffix the list yields for a domain. For the following
test descriptions, let `is_public_suffix(domain)` be a function that returns a bool representing whether the domain is
itself a public suffix.

These tests exercise the public suffix lookup directly rather than through a connection string.

### 1. A multi-label ordinary rule

This test utilizes the rule `com.ac` in the PSL. Assert that `is_public_suffix("com.ac") -> true` and
`is_public_suffix("foo.com.ac") -> false`.

### 2. A shorter wildcard rule

This test utilizes the rule `*.ck` in the PSL. Assert that `is_public_suffix("b.ck") -> true` and
`is_public_suffix("a.b.ck") -> false`.

### 3. A longer wildcard rule

This test utilizes the rule `*.nom.br` in the PSL. Notably there is a shorter rule, `.br` that shouldn't be used here.
Assert that `is_public_suffix("abc.nom.br") -> true` and `is_public_suffix("x.abc.nom.br") -> false`.

### 4. An exception rule

This test utilizes the rule `!www.ck` in the PSL, which overrides the `*.ck` rule. Assert that
`is_public_suffix("ck") -> true` and `is_public_suffix("www.ck") -> false`.

### 5. No rule matches

When no rule matches, the prevailing rule is `*` and the rightmost label alone is the public suffix. Assert that
`is_public_suffix("nosuchtld") -> true` and `is_public_suffix("foo.nosuchtld") -> false`.

### 6. An internationalized rule

This test utilizes the rules `рф` and `公司.cn` in the PSL, which are stored as Unicode while the hostnames being compared
are Punycode-encoded. Assert that `is_public_suffix("xn--p1ai") -> true`,
`is_public_suffix("example.xn--p1ai") -> false`, and `is_public_suffix("xn--55qx5d.cn") -> true`.

## Connection String Tests

The `srvAllowedHostsSuffix-psl-*` tests in the
[Initial DNS Seedlist Discovery tests](https://github.com/mongodb/specifications/tree/master/source/initial-dns-seedlist-discovery/tests/replica-set)
cover the two cases that are observable through a connection string: a suffix that is a public suffix (`cc`) is
rejected, and one that is not (`10gen.cc`) is accepted.

They live with the seedlist discovery tests because `srvAllowedHostsSuffix` is a connection string option, so a driver
should implement the parsing of the PSL and the uri option together.
