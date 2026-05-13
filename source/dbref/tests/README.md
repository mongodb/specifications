# DBRef Tests

These tests cover driver-level DBRef **model** encoding and decoding behavior. They do not require a running MongoDB
server.

## Relationship with bson-corpus

`source/bson-corpus/tests/dbref.json` already tests DBRef at the **BSON/Extended JSON layer**: it verifies that specific
byte sequences round-trip correctly through a driver's BSON codec. Documents with missing `$id`, non-string `$ref`, etc.
appear there as *valid BSON documents* — because they are valid BSON; the bson-corpus does not prescribe driver model
behavior.

The tests in this directory complement bson-corpus by testing the **driver model layer**:

| Concern                                                                | bson-corpus | These tests |
| ---------------------------------------------------------------------- | ----------- | ----------- |
| BSON bytes ↔ Extended JSON round-trip                                  | ✓           | —           |
| Driver decodes valid DBRef into a model object                         | —           | ✓           |
| Driver exposes `$ref`, `$id`, `$db`, extra fields                      | —           | ✓           |
| Driver rejects invalid documents (missing `$id`, wrong types)          | —           | ✓           |
| Out-of-order fields decoded and re-encoded in canonical order          | —           | ✓           |
| Encoding produces canonical field order (`$ref`, `$id`, `$db`, extras) | —           | ✓           |

## Test files

- `valid-documents.json` — Documents that MUST be decoded to a DBRef model.
- `out-of-order.json` — Documents with fields in non-canonical order that MUST still decode to a DBRef model and MUST
    re-encode with fields in canonical order.
- `invalid-documents.json` — Documents that MUST NOT be decoded to a DBRef model.
- `encoding.json` — DBRef models (constructed directly or via decoding) that MUST encode with fields in canonical order.

## Format

### Decoding tests (`valid-documents.json`, `out-of-order.json`, `invalid-documents.json`)

```json
{
  "description": "...",
  "tests": [
    {
      "description": "...",
      "document": { ... },
      "valid": true,
      "decoded": {
        "ref": "...",
        "id": ...,
        "db": null,
        "extra": { ... }
      }
    }
  ]
}
```

`document` is the input, expressed as Extended JSON (Relaxed). When `valid` is `true`, `decoded` contains the expected
field values of the resulting DBRef model. When `valid` is `false`, the document MUST NOT be decoded to a DBRef model.

### Encoding tests (`encoding.json`, `out-of-order.json`)

```json
{
  "description": "...",
  "tests": [
    {
      "description": "...",
      "input": { ... },
      "encoded": { ... }
    }
  ]
}
```

`input` is the document to decode into a DBRef model (possibly with out-of-order fields). `encoded` is the expected
output when the DBRef model is re-encoded to BSON, expressed as Extended JSON in canonical field order (`$ref`, `$id`,
`$db`, then extra fields).
