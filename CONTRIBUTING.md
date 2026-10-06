# Specification standards

This document describes the shared standards for all specifications contained within this repository. These standards
apply to all specification prose, pseudocode, tests, and comments, both human and machine-authored. Use these guidelines
both when writing and reviewing specification changes.

This is a living document: when an issue or difference of opinion occurs several times across reviews, the final
resolution SHOULD be added as a new guideline here.

## Style and formatting

- All prose MUST use proper English grammar: write in complete sentences, start with a capital letter, use correct
    punctuation, and end with a period. [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt) terms defined in a
    specification's `META` section are exempt.
- Authors MUST avoid metaphors, similes, analogies, and other figurative language.
- Authors MUST use numbered lists for enumerating steps in a process.
- Authors MUST use bulleted lists for enumerating related but unordered lists of items.

## RFC 2119 keywords

- Authors MUST use "MUST" wherever alignment of drivers across languages is required.
- Authors MUST use "SHOULD" only when valid exceptions to a requirement exist and can be documented.
- When in doubt, authors MUST use "MUST" instead of "SHOULD".

## Pseudocode

- Authors SHOULD add pseudocode following a numbered list of MUST steps that defines an algorithm or a description of a
    schema.
- Comments MUST follow the standards above for prose style.
- Authors MUST use Python syntax for algorithms and Typescript syntax for BSON and wire documents.
- Pseudocode MUST be purely explanatory, not normative. It cannot substitute for a prose description of a required
    behavior.

## Tests

- Tests MUST cover every behavior required in the specification.
- Authors SHOULD use unified tests over prose tests whenever possible.
    - Authors SHOULD prefer unified tests over new test formats.
    - Authors SHOULD expand unified test capabilities over prose tests where expansion would permit the testing of new
        behaviors.
- Authors MUST specify all environmental and topological requirements for each test.
- Authors MUST NOT assume a specific driver architecture when creating tests unless that architecture is explicitly
    required by the specification.
- Tests MUST be in a separate `tests/` directory within specification directory, not in the specification itself.
    - Prose tests MUST be in a `tests/README.md` file.
    - Unified tests MUST be in a `tests/unified` subdirectory.

## Changelog

- All changes MUST have a changelog entry in the modified specification.
- Changelog entries MUST be concise summaries of their described changes.
- Changelog entries MUST be in reverse chronological order, with the latest change at the top.
- Each entry MUST follow a standard format: `YYYY-MM-DD: Description.`, and MUST be separated from its neighbors by a
    blank line.

## Links

- Cross-spec links MUST use relative paths instead of absolute ones.
- Terms defined in another specification MUST be linked instead of re-defining.

## Deprecation

- Deprecated features MUST be marked as deprecated and removed entirely from the specification once no driver + server
    pair supports them.

## Document Structure

- Specifications MUST use the following sections, in this order, when present. Abstract, META, Specification, and
    Changelog are required.

```
## Abstract 

A brief description of the specification's intent and why it requires its own specification.

## META 

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Terms 

Definitions of all technical terms used in the specification.

## Specification 

The bulk of the document. Contains all actual requirements and the use of keywords defined in the META section.

## Implementation Notes

Guidance for driver authors specific to actual implementation. This can include allowances for language differences, examples of non-obvious complexity in code, and the like.

## Design Rationale

Motivations for the design choices made in the specification. Answer the "why" of choices, not the "how".
If there are notable rejected designs, include brief explanations for their rejection in a "Rejected Alternatives" subsection.

## Backwards Compatibility 

Implications of the specification for older driver and server versions that do not support its changes.

## Reference Implementation 

The drivers responsible for producing the initial reference implementation of the specification.

## Future Work 

Future additions to the specification that did not qualify for the initial version.

## Questions and Answers 

Answers to questions that have or will frequently come up for driver authors working to implement or understand the specification.

## Test Plan 

A link to the separate test document associated with the specification.

## Changelog

A dated, bulleted list of changes made to the specification.
```

## LLM usage

- Authors MUST be responsible for and own all changes made under their name, regardless of how they were created.
