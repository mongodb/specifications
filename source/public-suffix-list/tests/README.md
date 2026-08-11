# Public Suffix List tests

These tests verify that drivers parse [public_suffix_list.dat](../public_suffix_list.dat) correctly by exercising the
`srvAllowedHostsSuffix` connection string option, which MUST NOT accept a value that is itself a public suffix.

Each case covers one of the three rule forms described in [Rule syntax](../public-suffix-list.md#rule-syntax):

| File                                       | Rule       | Form           | Accepted |
| ------------------------------------------ | ---------- | -------------- | -------- |
| `srvAllowedHostsSuffix-ordinary-rule.yml`  | `dr.in`    | Ordinary rule  | No       |
| `srvAllowedHostsSuffix-wildcard-rule.yml`  | `*.nom.br` | Wildcard rule  | No       |
| `srvAllowedHostsSuffix-exception-rule.yml` | `!www.ck`  | Exception rule | Yes      |

The wildcard case is the interesting one for parsing: `abc.nom.br` does not appear literally in the list, so a driver
that only does exact matching will incorrectly accept it. The exception case is the inverse: `www.ck` matches the
wildcard rule `*.ck`, so a driver that ignores exception rules will incorrectly reject it.

## Test Format and Use

These files use the test format and DNS setup defined by the
[Initial DNS Seedlist Discovery tests](../../initial-dns-seedlist-discovery/tests/README.md); see that document for the
meaning of each field and for the SRV and TXT records that must be configured.

The `srvAllowedHostsSuffix-exception-rule.yml` case omits `hosts` and sets `ping` to false because it asserts only that
the connection string is accepted and that the SRV records resolve to the expected seeds. That assertion does not depend
on the topology under test, so unlike the seedlist discovery tests these files are not split into `replica-set`,
`sharded`, and `load-balanced` directories.
