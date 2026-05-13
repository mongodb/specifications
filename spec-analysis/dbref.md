# Analysis: dbref

## Missing Tests

- [ ] Valid `DBRef` with only `$ref` and `$id` MUST decode to `DBRef` model — basic decoding
- [ ] Valid `DBRef` with different `$id` types (ObjectId, integer, null) MUST decode — type acceptance
- [ ] Valid `DBRef` with optional `$db` MUST decode — three-field structure
- [ ] `DBRef` with extra optional fields MUST decode; model MUST provide access to those fields
- [ ] Out-of-order fields MUST be implicitly decoded to `DBRef` model — field-order normalization
- [ ] Document missing `$ref` MUST NOT be implicitly decoded
- [ ] Document missing `$id` MUST NOT be implicitly decoded
- [ ] `$ref` with a non-string type MUST NOT decode
- [ ] `$db` with a non-string type MUST NOT decode
- [ ] `DBRef` MUST encode fields in order: `$ref`, `$id`, `$db`, then extra fields
- [ ] Out-of-order fields decoded from BSON MUST be re-encoded in canonical order
- [ ] Extra field order MUST be preserved relative to one another
- [ ] Any BSON type MUST be accepted for `$id` during decoding
- [ ] No naming restrictions on `$ref`/`$db` strings (dots, dollar signs)
- [ ] Extra fields may include dollar-prefixed names (`$foo`)
- [ ] Extra fields may include dot-notation names (`foo.bar`)

## Ambiguities

- **Explicit vs implicit decoding boundary**: "If a BSON document cannot be implicitly decoded, leave it as-is. If it
    cannot be explicitly decoded, raise an error." The boundary between "cannot" (structural issue) and "invalid"
    (semantic issue) is unclear.
- **Inheritance (SHOULD)**: "DBRef model SHOULD inherit the class used to represent embedded documents" — does "SHOULD"
    mean optional? If no inheritance, how does the driver provide access to extra fields?
- **Extra field order ("SHOULD attempt to preserve")**: What does "attempt" mean in practice? Is this best-effort? What
    if the language runtime cannot preserve insertion order?

## Inconsistencies

- **`$id` restrictions at construction vs decoding**: Construction says "SHOULD NOT enforce restrictions" on `$id`
    (weak), but decoding says "MUST accept any BSON type" (strong). Different normative levels for the same concept.
- **Test plan conditionality**: "Tests only relevant to drivers that provide a DBRef model class" but then "Drivers
    SHOULD implement these tests for both explicit and implicit decoding code paths as needed." If decoding is not
    mandatory, why are tests mandated?

## Notes

- No `tests/` directory; tests are prose-only.
- Good use of Extended JSON examples, but these require manual translation to BSON in driver test implementations.
- Design Rationale explains robustness principle: liberal decoding (accept out-of-order fields), conservative encoding
    (canonical order output).
