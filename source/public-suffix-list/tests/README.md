# Public Suffix List tests

These tests verify that a driver determines the public suffix of a domain correctly, as described in
[Determining the public suffix](../public-suffix-list.md#determining-the-public-suffix).

## Prose Tests

Each test below states the case being covered, then the public suffix the list yields for a domain. For the following
test descriptions, let `is_public_suffix(domain)` be a function that returns a bool representing whether the domain is
itself a public suffix.

These tests exercise the lookup directly rather than through a connection string.

1. A single-label ordinary rule. `10gen.cc` has the public suffix `cc`, since only the parent is in the list. Assert
    that `is_public_suffix("cc") -> true` and `is_public_suffix("10gen.cc") -> false`.
2. A multi-label ordinary rule, matched in preference to the shorter `ac`. `foo.com.ac` has the public suffix `com.ac`.
    Assert that `is_public_suffix("com.ac") -> true` and `is_public_suffix("foo.com.ac") -> false`.
3. A wildcard rule, `*.nom.br`, matching a value that does not appear literally in the list, so a driver that only
    compares for equality will not find it. A `*` matches exactly one label, so the rule does not extend to cover `x`:
    `x.abc.nom.br` has the public suffix `abc.nom.br`. Assert that `is_public_suffix("abc.nom.br") -> true` and
    `is_public_suffix("x.abc.nom.br") -> false`.
4. A wildcard rule, `*.ck`, with no exception rule applying. `a.b.ck` has the public suffix `b.ck`. Assert that
    `is_public_suffix("b.ck") -> true` and `is_public_suffix("a.b.ck") -> false`.
5. An exception rule, `!www.ck`, prevailing over `*.ck` and having its leftmost label removed. `www.ck` has the public
    suffix `ck`, even though `ck` is not itself a rule in the list. Assert that `is_public_suffix("ck") -> true` and
    `is_public_suffix("www.ck") -> false`.
6. No rule matches, so the prevailing rule is `*` and the rightmost label alone is the public suffix. `foo.nosuchtld`
    has the public suffix `nosuchtld`. Assert that `is_public_suffix("nosuchtld") -> true` and
    `is_public_suffix("foo.nosuchtld") -> false`.

## Connection String Tests

The `srvAllowedHostsSuffix-psl-*` tests in the
[Initial DNS Seedlist Discovery tests](../../initial-dns-seedlist-discovery/tests/replica-set) cover the two cases that
are observable through a connection string: a suffix that is a public suffix (`cc`) is rejected, and one that is not
(`10gen.cc`) is accepted. Both use a suffix the test SRV hosts end with, so the host suffix check passes and the public
suffix check is the only thing that can change the outcome.

They live with the seedlist discovery tests because `srvAllowedHostsSuffix` is a connection string option, so a driver
implements the parsing of the PSL and the uri option together.
