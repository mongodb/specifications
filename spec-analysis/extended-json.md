# Analysis: extended-json

## Missing Tests

Testing is explicitly delegated to the **BSON Corpus Test Suite** (`source/bson-corpus/`). No local test files are
expected. However, the following behaviors may lack coverage there:

- [ ] UUID parsing: accept with or without hyphens (section "Special rules for parsing `$uuid` fields")
- [ ] Type wrapper validation: reject objects with missing or extra keys for type wrappers (except `DBRef`)
- [ ] Non-finite numeric values: `Infinity`, `-Infinity`, `NaN` for `Double` and `Decimal128`
- [ ] Relaxed JSON number interpretation: non-integers → `Double`; integers → smallest representable BSON integer type
- [ ] Key order in Canonical format: keys emitted in the order described in the Conversion table
- [ ] Hex string case-insensitivity: parsers accept both cases; generators emit lowercase
- [ ] Nesting depth: parsers support ≥200 levels; generators support ≥100 levels

## Ambiguities

- **Regular Expression Conversion table**: Column header shows `{pattern:` without a closing quote — Markdown rendering
    is ambiguous. Should clarify whether `pattern` requires quotes (it should per the example on the corresponding
    line).
- **Legacy Extended JSON conditional (lines 181–182)**: "Unless configured to allow Legacy Extended JSON, in which case
    it SHOULD follow these rules" — the SHOULD is ambiguous. Should be clarified as MUST or explicitly made optional.
- **"Smallest BSON integer type" (lines 212–216)**: "Smallest" could mean smallest by byte size (Int32 before Int64) or
    the smallest type that can hold the value. Needs clarification for implementers.

## Inconsistencies

- **Non-finite Double asymmetry**: Finite doubles are relaxed to bare JSON numbers, but non-finite doubles remain as
    `{"$numberDouble": "..."}` even in Relaxed format. This is correct behavior but is not explicitly highlighted as
    intentional — could surprise implementers.

## Notes

- RST redirect at `source/extended-json.rst` — can be cleaned up.
- Reference implementation stubs (lines 618–629: "needs to be updated" / "TBD") are outdated and should be removed.
- No `## Changelog` section in the spec file.
