# Specification standards

This document describes the shared standards for all specifications contained within this repository. These standards
apply to all specification prose, pseudocode, tests, and comments, both human and machine-authored. Use these guidelines
both when writing and reviewing specification changes.

This is a living document: when an issue or difference of opinion occurs several times across reviews, the final
resolution SHOULD be added as a new guideline here.

## Repository structure

- All specifications MUST go in the `source/` directory under their own subdirectory (e.g `source/auth/`).

## Style and formatting

- All prose MUST use proper English grammar: write in complete sentences, start with a capital letter, use correct
    punctuation, and end with a period. [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt) terms defined in a
    specification's `META` section are exempt.
- Authors MUST avoid metaphors, similes, analogies, and other figurative language.
- Authors MUST use numbered lists for enumerating steps in a process.
- Authors MUST use bulleted lists for enumerating related but unordered lists of items.
- All specifications MUST use [GitHub Flavored Markdown](https://github.github.com/gfm/) and follow the
    [MongoDB Documentation Style Guidelines](https://www.mongodb.com/docs/meta/style-guide/) with a 120-line character
    limit.
- Authors MUST abide by the automated linters described in [README.md](./README.md).

## RFC 2119 keywords

- Authors MUST use "MUST" wherever alignment of drivers across languages is required.
- Authors MUST use "SHOULD" only when valid exceptions to a requirement exist and can be documented.
- When in doubt, authors MUST use "MUST" instead of "SHOULD".
- Authors MUST follow [RFC 8174](https://www.rfc-editor.org/info/rfc8174/) and use all-caps when invoking RFC 2119
    keywords.

## Pseudocode

- Authors SHOULD add pseudocode following a numbered list of MUST steps that defines an algorithm or a description of a
    schema.
- Comments MUST follow the standards above for prose style.
- Authors MUST use Python syntax for algorithms and Typescript syntax for BSON and wire documents.
- Pseudocode MUST be purely explanatory, not normative. It cannot substitute for a prose description of a required
    behavior.

## Tests

- Tests MUST cover every behavior required in the specification.
- Tests MUST only verify functionality directly related to their specification. Omit irrelevant fields in expected
    output.
- Authors SHOULD use unified tests over prose tests whenever possible.
    - Authors SHOULD prefer unified tests over new test formats.
    - Authors SHOULD expand unified test capabilities over prose tests where expansion would permit the testing of new
        behaviors.
- Authors MUST number prose tests starting with `1.`.
- Authors MUST add new tests to the end of list of prose tests.
- Authors MUST not modify existing tests unless to fix correctness issues. Create new tests instead of modifying
    existing ones.
- Authors MUST specify all environmental and topological requirements for each test.
- Authors MUST NOT assume a specific driver architecture when creating tests unless that architecture is explicitly
    required by the specification.
- Tests MUST be in a separate `tests/` directory within specification directory, not in the specification itself.
    - Prose tests MUST be in a `tests/README.md` file.
    - Unified tests MUST be in a `tests/unified` subdirectory.
- Authors MUST not remove deprecated prose tests, but instead strike through their content or otherwise explicitly mark
    them as such.
- Authors MUST use `runOnRequirements` (for unified tests) or instructions on skipping (for other tests) to ensure tests
    are only executed when supported.
- Tests not run by any driver MUST be deleted.
- Unified tests MUST use the lowest possible schema version that satisfies their requirements.
- Tests MUST verify or explicitly exclude behavior for all four supported topologies: standalone, replica set, sharded
    cluster, and load balanced.
- Authors MUST make manual changes to `.yml` test files and then generate the `.json` versions using
    [these instructions](./README.md#converting-to-json).
- Authors MUST NOT make manual changes to `.json` test files generated from a `.yml` source.

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

- Deprecated features MUST be marked as deprecated and removed entirely from the specification once no driver and server
    pair supports them.
- When retiring an EOL server version, authors MUST remove all version-gated tests, prose, and pseudocode specific to
    the EOL version. Use the `retiring-server-versions` skill as a starting point.

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

- Authors MUST take responsibility for and own all changes made under their name, regardless of how they were created.

## PR Requirements

- PR titles MUST include a DRIVERS ticket (e.g., `DRIVERS-1234`).
- Authors MUST test changes in at least one language driver.
- Authors MUST include links to the driver implementation PRs in the PR description (e.g.,
    `Python implementation: https://github.com/mongodb/mongo-python-driver/pull/…`).
- Tests MUST pass against all supported server versions and topologies.
