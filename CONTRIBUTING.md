# Specification standards

This document describes the shared standards for all specifications contained within this repository. These standards
apply to all specification prose, pseudocode, tests, and comments, both human and machine-authored. Use these guidelines
both when writing and reviewing specification changes.

This is a living document: when an issue or difference of opinion occurs several times across reviews, the final
resolution should be added as a new guideline here.

## Style and formatting

- All prose must use proper English grammar: write in complete sentences, start with a capital letter, use correct
    punctuation, and end with a period.
- Avoid metaphors, similes, analogies, and other figurative language.
- Use numbered lists for enumerating steps in a process.
- Use bulleted lists for enumerating related but unordered lists of items.

## Pseudocode

- Consider adding pseudocode following a numbered list of MUST steps that defines an algorithm or system.
- Comments must follow the standards above for prose style.
- Use Python syntax for algorithms, Typescript syntax for BSON and wire documents, and plain text for systems.

## Tests

- Prefer unified tests over prose tests whenever possible.
- Specify all environmental and topological requirements for each test.
- Tests belong in a separate `tests/README.md` file within the specification directory, not in the specification itself.

## Changelog

- All changes require a changelog entry in the modified specification.
- Changelog entries are concise summaries of their described changes.
- Changelog entries are in reverse chronological order, with the latest change at the top.
- Each entry follows a standard format: `YYYY-MM-DD: Description.`, and is separated from its neighbors by a blank line.

## Links

- Cross-spec links use relative paths instead of absolute ones.
- Link to terms defined in another specification instead of re-defining.

## Deprecation

- Mark deprecated features as deprecated and remove them entirely from the specification once no driver + server pair
    supports them.

## Document Structure

- All specifications must be written exclusively using the following required sections in the order they appear in:

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

## Rationale 

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

- All changes are owned by and are the responsibility of the author, regardless of how they were created.
