---
name: retiring-server-versions
description: >-
  Use when raising the minimum supported MongoDB server version in this repository (e.g. EOL'ing an old server
  version) and needing to find and remove now-dead version-gated tests, prose, and pseudocode across the whole
  specifications repo.
---

# Retiring Server Versions

## Overview

Raising the minimum-supported-server-version floor doesn't just delete a few "if version < X" branches — it leaves
behind scattered dead conditionals, vacuous qualifiers, unrunnable tests, and stale prose across the whole repository.
The single biggest failure mode is scoping the cleanup too narrowly (to files already touched, or to obvious `< X.Y`
patterns) and then discovering — repeatedly, across multiple review rounds — that reviewers keep finding whole files and
whole *categories* of miss that the first pass never looked for.

**Core principle:** Establish fix/leave criteria explicitly before editing, sweep the *whole* repo (not just
already-changed files) with a wide pattern net, verify judgment calls against ground truth (real driver source), and
expect to re-sweep every time a reviewer finds a new *shape* of miss — not just patch the one instance.

## When to Use

- You're working a ticket to remove old server version references (e.g. `DRIVERS-XXXX` "Remove pre-N.N references from
    specs and tests").
    - Only expected once *all* drivers have dropped support for the old server (e.g. `DRIVERS-XXXX` "Mark Server version
        N.N as EOL" is complete). Drivers that track this repo via a git submodule pick up test deletions as soon as they
        bump the submodule, so removing tests ahead of the EOL silently drops coverage for drivers that still support the
        old version.
- You're removing dead version-gated conditionals, fallback branches, or "only applies to old versions" prose.
- A reviewer keeps finding pre-floor references you thought you'd already cleaned up.

**Not for:** routine deprecation of a single feature/API (that's a normal spec change); one-off version bumps with no
conditional logic to clean up.

## Step 1: Determine the Old Floor and Confirm Scope

Don't assume you know what the previous minimum version was, and don't assume this is the first such cleanup.

- Grep git log for the most recent prior cleanup of this kind, e.g.
    `git log --all --oneline -i --grep="pre-.*version\|remove.*pre-\|minimum.*server.*version"` (adjust to match this
    repo's actual commit-message conventions), to find the last "remove pre-X.Y references" effort and see what floor it
    targeted.
- State the inferred old floor to the operator explicitly and get confirmation before scoping any work — don't proceed
    on an assumption.
- The new floor is normally given by the task/ticket (e.g. `DRIVERS-XXXX` "remove pre-4.4 references"). If it isn't
    stated, ask the operator directly — don't infer it as simply "the next version after the old floor." Server versions
    don't always retire in strict sequence, and guessing wrong scopes the entire cleanup incorrectly.
- If the inferred old floor is more than one version below the new floor (e.g. the last cleanup only reached pre-4.0,
    but the floor is now 4.4 — meaning pre-4.2 was never actually done), don't bundle multiple version retirements into
    one pass. Do them one at a time (pre-4.2 first, then pre-4.4 as its own follow-up), each as its own ticket/PR.
    Bundling makes it impossible to tell which removal was justified by which version bump, and produces a much larger,
    harder-to-review diff.

## Step 2: Agree on Fix/Leave Criteria Before Editing

Before editing anything, get explicit agreement on two buckets. Getting this wrong costs far more time than getting it
right up front.

**FIX (dead weight at the new floor):**

- Normative MUST/MUST NOT behavior, tests, or pseudocode conditioned on a version/wire-version below the new floor
- "X.Y or higher/later/+" qualifiers — check both *below* the new floor AND *exactly at* it. A "4.2 or higher" qualifier
    is just as dead as "3.6 or higher" once 4.2 *is* the floor. This exact-at-floor case is the most commonly missed
    pattern — treat it as a first-class search target, not an afterthought.
- Fallback/legacy branches for capabilities/fields that can no longer be absent (e.g. a hello-response field that's now
    always present)
- `Minimum Server Version` metadata line (a `- Minimum Server Version: X.Y` bullet under the doc's H1, not YAML
    frontmatter) below the new floor (repo convention: remove the line entirely, don't bump it to the new floor, unless
    the spec's own minimum is a genuinely feature-specific requirement, e.g. CSFLE's 4.2)
- Unrunnable test instructions (requires a server version that no longer exists, or a mechanism removed *before* the
    floor — e.g. `MONGODB-CR`, removed in 4.0, below a 4.2 floor)

**LEAVE (keep as-is):**

- Historical narrative ("Version X introduces...", Abstracts, Motivation/Design Rationale/Q&A sections, `@since`
    annotations)
- Version boundaries between two versions that are **both still supported** (e.g. "4.2 to 5.0" when the floor is 4.2 —
    this is a real, meaningful boundary, not vacuous)
- `minServerVersion` values in `runOnRequirements` test gates, regardless of value — a floor below the new minimum is
    trivially satisfied by every supported server, so the test keeps running fine; leave it (confirm this policy with
    the repo owner; it was the explicit ruling last time). **This does NOT extend to `maxServerVersion`** — see Step 4's
    "Unrunnable YAML tests and files" section; a `maxServerVersion` below the new floor makes the test permanently
    unrunnable and must be handled as a FIX, not left alone.
- Features/commands removed **at** the new floor, not before it (e.g. `copydb` removed exactly at 4.2 is out of scope
    for a "remove pre-4.2 references" pass — same bucket as anything at/above the floor)
- Deliberately-invalid schema fixtures under `source/unified-test-format/tests/invalid/`. These hardcode nonsense
    versions (`maxServerVersion: 0`, `minServerVersion: "1.2.3.4"`) precisely to prove the schema rejects them. Because
    they sit below *every* conceivable floor, they match the `maxServerVersion` sweep in Step 4 on every retirement,
    forever, and look exactly like dead weight — but deleting them breaks schema validation. Verified: they surface only
    in the `maxServerVersion` sweeps, not in the numeric or table-cell searches.

Capture ambiguous cases as a third "borderline" bucket for human triage rather than guessing either direction.

## Step 3: Sweep the Whole Repo — Never Just the Diff

The single most common failure: scoping the search to `git diff <base> --name-only`. Every review round found files
*outside* that diff — including specs never touched at all in earlier passes (`uri-options.md`, `max-staleness.md`,
`server-selection.md`, `OP_MSG.md`). Always grep the entire repository under `source/`, every pass, even (especially) on
follow-up passes after the first round looked done.

## Step 4: Cast a Wide Pattern Net

Each of the following is a distinct *shape* of hit that requires its own search — do not assume one regex catches all of
them. Read 10+ lines of context around every hit before classifying it (most hits in this repo are legitimate historical
narrative, not dead code); never classify from the grep line alone.

Bias every pattern below toward recall over precision: a false positive costs a few extra seconds of reading and
discarding; a false negative silently drops a real dead reference from the sweep, which is exactly the failure mode this
whole skill exists to prevent. Some commands below will also match a patch version (e.g. `< 4.2.9`, `pre-4.2.9`) — don't
try to exclude that with lookarounds; it's a feature, not noise, since a patch-specific dead reference (e.g. a bug that
only affected `4.2.0`-`4.2.5`) is exactly the kind of hit you need to see and classify, not filter out. Multi-digit
collisions like `14.2` are excluded by the *left*-anchored patterns (`<`, `pre-`, since the anchor must sit immediately
before the digit) but NOT by the *right*-anchored ones (`+`, `or higher` — e.g. `14.2+` and `14.2 or higher` both still
match, since nothing constrains what precedes the number). No shipped MongoDB release creates such a collision today,
but that expires once the server reaches double-digit majors — a `5.0` retirement collides with `15.0`, a `6.0` one with
`16.0`. Don't assume all four patterns are equally guarded; they aren't. If the colliding version exists by the time you
read this, add an explicit left guard — `(^|[^0-9])` — to the right-anchored patterns only.

### Numeric comparisons

This is one single-floor pass (see Step 1 — don't bundle separate floor-raises together), and you already know both
numbers involved: the old floor being retired (e.g. 4.2) and the new floor (e.g. 4.4). Don't search broadly across every
historical version; that mostly re-surfaces content from *previous* retirements that was already correctly classified as
historical narrative last time (tested: a broad `< ?[0-9]+\.[0-9]+` search here returns roughly half noise — unrelated
numeric comparisons, other libraries' version checks, and legitimate current boundaries well above the new floor — while
the scoped version below loses no real hits). Scope the search to just the two numbers in play, and include `<=`
alongside `<` — a bare `< ?` anchor misses `<=` entirely, and this repo has a real, currently-live example
(`MongoDB \<= 4.2, a monitor uses the Polling Protocol...` in `server-monitoring.md`) that only the `<=?` form catches.
Note the backslash in that quote is really on disk, not a typo: `mdformat` escapes a bare `<` in prose as `\<`. The
patterns below still match it (`<=` is a substring of `\<=`), but don't anchor a pattern to a character immediately
preceding `<`, and expect `\<` in the grep output.

```
grep -rnE "<=? ?(4\.2|4\.4)\b" source --include="*.md"
grep -rnE "\bpre-?(4\.2|4\.4)\b" source --include="*.md"
```

(substitute your own old-floor/new-floor numbers for `4\.2`/`4\.4`). The first is nearly clean. The second is noisier —
most of its hits are `## Changelog` entries like "Remove pre-4.2 version references," which are never in scope (see Step
2). Both commands can surface Changelog hits (e.g. "2020-01-10: Error if hint specified... for servers < 4.2"); skip
anything inside a Changelog section before reading further, for either command. The English-language equivalents ("older
than", "prior to") are much lower precision as bare phrases — tested samples were mostly unrelated to server versions at
all (e.g. "prior to each test run", "prior to garbage collection") — so treat them as a supplementary spot-check, not a
primary tool.

### "X.Y or higher/+" qualifiers — check both below the floor and at it

Same reasoning as above — scope to the two numbers in play, not every historical version:

```
grep -rnE "(4\.2|4\.4)\+" source --include="*.md"
grep -rnE "(4\.2|4\.4) or (higher|later|newer|greater|above)" source --include="*.md"
```

(substitute your own old-floor/new-floor numbers). Tested clean in this repo; the broad, number-agnostic version returns
several times as many hits, and the extra ones are entirely legitimate current-and-above-floor content like "server
7.0+" or "9.0+", not dead weight for this retirement. Classify every hit against the new floor explicitly — a hit whose
number equals the new floor exactly (e.g. "4.4 or higher" when 4.4 *is* the new floor) is just as dead as one below it,
but easy to overlook because the number looks current at a glance. Treating "at the floor" hits as their own deliberate
pass, not an afterthought, is the single most commonly skipped step.

### Wire-version proxies, spelled out

Wire version numbers are too short to grep for bare — a bare `9` returns hundreds of unrelated line/port/byte-count
hits. Anchor to the word instead, and search both wire versions in play (the retiring version's and the new floor's),
mirroring the two-number scoping used everywhere else in this step:

```
grep -rnE "(wire ?[Vv]ersion|[Mm]ax[Ww]ireVersion|[Mm]in[Ww]ireVersion)['\"]? *(is |>=? ?|<=? ?|of |as )?(8|9)\b" source --include="*.md"
```

Substitute the two wire versions you're retiring across (here `8` = server 4.2 and `9` = server 4.4). Keep the trailing
`\b`: it's what stops `9` from matching inside `93`, and it matters more, not less, for multi-digit wire versions.

Zero hits is a common and usually genuine result — only a handful of wire numbers are spelled out in prose anywhere in
this repo. Before trusting a zero, confirm your two numbers rather than your regex: **the canonical table can lag the
server.** As of this writing it stops at 8.0 (wire 25) and has no row for 9.0 at all, even though ~22 files already
reference 9.0 — so an 8.0 retirement cannot look its new floor up there. If your version is missing from the table, take
the number from the server's `releases.yml` (linked at the bottom of that file) and consider adding the missing row as a
separate PR; do not extrapolate it.

**Never compute a wire version from a server version — always look it up** in the canonical table at
[`source/wireversion-featurelist/wireversion-featurelist.md`](../../../source/wireversion-featurelist/wireversion-featurelist.md).
Two traps make arithmetic actively wrong from 5.0 onward:

- **They go multi-digit.** Server 4.4 is wire 9, but 5.0 is wire **13** — so a pattern written as a single trailing
    digit stops working the moment you retire 4.4 or later.
- **The sequence has gaps.** 4.4 → 5.0 skips wire 10–12, and 6.2 → 7.0 skips wire 20. There is no reliable offset to
    add; since server 5.1 the wire version is derived from the number of releases since 4.0, not from the version
    number.

That table file is itself out of scope for this cleanup — it's inherently a version-mapping reference, not a version
gate.

### Table cells / structured data

Prose-oriented regexes miss a bare version number sitting alone in a table column. Anchor to the pipe delimiter instead,
repo-wide like every other search in this step (not scoped to one file you already suspect — that defeats Step 3's
"sweep the whole repo" rule):

```
grep -rnE '\|\s*(4\.2|4\.4)' source --include="*.md"
```

(substitute your own retiring/new-floor numbers, exactly as in the patterns above — don't broaden this to a digit range
like `[2-4]\.[0-9]`. A range re-surfaces every historical version's table rows, which Step 4's opening argument already
rejects, and it silently matches nothing once you're retiring 5.0 or later.) Expect
`wireversion-featurelist/wireversion-featurelist.md` to dominate the hits; it is out of scope by definition (see
"Wire-version proxies" above), so skip it and read the rest.

### Comments inside YAML test files

Apply every pattern above to `.yml` comments too, not just markdown prose — it's the same dead content in a different
file type. Extend `--include` accordingly (e.g. `--include="*.yml"`) when re-running any of the searches above.

### Unrunnable YAML tests and files

This is a distinct action, not just another search pattern — `minServerVersion` and `maxServerVersion` don't behave the
same way under a floor raise. A `minServerVersion` below the new floor is harmless (trivially satisfied by every
supported server; see Step 2 LEAVE). A `maxServerVersion` below the new floor is the opposite: the test can **never run
again against any supported server**, and must be removed — this is the single largest category of work in a typical
retirement (the original pre-4.2 cleanup this skill is modeled on deleted ~26 whole files and ~28 individual tests this
way).

`runOnRequirements` can appear at two levels, and the correct action differs:

- **File-level** (top of the file, before any `tests:` key) — the *entire file* is dead. Delete both the `.yml` and its
    paired `.json`.
- **Per-test** (nested under one entry inside the `tests:` array) — only *that test* is dead; remove just that entry and
    leave the rest of the file alone.

Find file-level candidates first (check these before the noisier per-test search, since a whole dead file makes any of
its per-test hits moot):

```
for f in $(grep -rl "maxServerVersion" source --include="*.yml"); do
  awk '/^tests:/{exit} /maxServerVersion/{print FILENAME": "$0}' "$f"
done
```

Then find per-test candidates in the remaining files:

```
for f in $(grep -rl "maxServerVersion" source --include="*.yml"); do
  awk '/^tests:/{flag=1} flag && /maxServerVersion/{print FILENAME": "$0}' "$f"
done
```

Both commands print *every* `maxServerVersion` line, not just dead ones — including ones at or above the new floor (e.g.
`maxServerVersion: "7.0.99"`), which are never in scope (see Step 2 LEAVE: at/above the floor is fine). Expect the raw
hit list to be several times larger than the real one; read each hit's value against the new floor to classify it. Only
after that filtering does a real file-level set emerge (e.g. `crud/tests/unified/deleteOne-hint-serverError.yml` with a
top-level `maxServerVersion: 4.3.3`), and note that a per-test hit rarely means the whole file is dead (e.g.
`insertOne-serverErrors.yml`, where only a minority of its tests are individually gated dead).

Unlike numbered markdown prose tests (Step 6 — mark `**Removed**`, never delete-and-renumber), these unified-test
entries are matched by description string, not by ordinal position, and aren't referenced by index across drivers — so
it's safe to delete them outright, no marker needed. Before deleting from a `.yml`, check whether it has a `.template`
source (see "Generated + `.template` file pairs" below) — if so, edit the template and regenerate rather than
hand-deleting the generated file directly.

### Illustrative examples citing the current floor

An example error message or scenario can hardcode today's specific numbers (e.g. "wire version 8... MongoDB 4.2") and go
stale when the floor moves, even though it isn't a live conditional. A bare search for the old floor's number is far too
noisy to use directly; narrow it to quoted/blockquote text, which is where hardcoded examples usually live:

```
grep -rnE '"[^"]*4\.2[^"]*"|>\s*".*4\.2' source --include="*.md"
```

(adjust `4\.2` to the old floor). This heuristic is not exhaustive — an example can appear outside quotes too — so still
read context around any bare-floor-number hits you find through other means; it just gives you a fast, low-noise
starting point instead of triaging the full bare-number hit list by hand.

### Stale identifier/file naming

Version numbers baked into names without a decimal point (`pre42`, `post_42`, files like `post-42-*.yml`) are invisible
to every dotted-version regex above, and a bare-digit content grep is unusably noisy (`42` also matches arbitrary
example values like `Int32: 42`). Search filenames and identifiers directly instead of file content:

```
find source -iname "*pre[0-9][0-9]*" -o -iname "*post[0-9][0-9]*" -o -iname "*pre-[0-9][0-9]*" -o -iname "*post-[0-9][0-9]*"
grep -rnE "def [a-zA-Z_]*(pre|post)_?[0-9]{2,}[a-zA-Z_]*\(" source --include="*.py"
```

The first finds filenames, the second finds generator function names. Both are zero-noise in this repo as of this
writing (they return exactly the known `post-42-*` cluster and its generator function, nothing else). Unlike the
patterns above, these are deliberately *not* scoped to the two versions in play — the whole point is to surface stale
names you don't already know about, and there are few enough to read by hand. Note the `{2,}` rather than `{2}`: an
undotted `10.0` is `100`, three digits, so a fixed two-digit quantifier would start missing names once the server
reaches double-digit majors. This is especially worth checking where a "pre-X" counterpart has already been removed,
since the surviving "post-X" name no longer makes sense on its own.

### Removed commands/mechanisms

These aren't discoverable by grep alone — you won't know their names in advance. Use `WebSearch` for MongoDB's official
"Compatibility Changes in MongoDB X.Y" release-note page for each major version between the old floor and the new floor
— don't assume a specific URL pattern will resolve directly (the release-notes site layout has changed and can
redirect); search for the page by title and follow the result. Each page enumerates exactly what was removed/changed in
that release. Confirm whether each removal landed *before* the new floor (in scope) or *at*/*after* it (out of scope,
same as anything at/above the floor), then grep the repo for the specific names you found. A "nothing removed at this
version is referenced in the repo" result is a legitimate, useful finding — don't treat an empty result as a failed
search.

### Generated + `.template` file pairs

Some YAML test files are generated, not hand-authored — check for a "Tests in this file are generated from
X.yml.template" comment at the top of the `.yml`, or a sibling file under `etc/templates/X.yml.template`. If you find
one, edit the `.template` source, not the generated `.yml` directly (a hand-edit to the generated file alone gets
silently overwritten the next time someone regenerates it), then regenerate.

Regeneration is two separate steps, and `make -C source` only does the second one:

1. **Template → `.yml`**: `make` does *not* process `.template` files. Each template family has its own generator
    script, and the authoritative list of them is the "Regenerate JSON test files" step in
    [`.github/workflows/unified-tests.yml`](../../../.github/workflows/unified-tests.yml) (e.g.
    `python3 ./source/client-side-operations-timeout/etc/generate-basic-tests.py ./source/client-side-operations-timeout/etc/templates ./source/client-side-operations-timeout/tests`).
    Run the script matching the template you edited, using that workflow's invocation verbatim rather than guessing
    at arguments. That workflow is also what regenerates these files in CI, so anything it doesn't run won't be
    regenerated automatically either.
2. **`.yml` → `.json`**: `make -C source` (this is all the Makefile does).

If either step fails, fix the tooling (e.g. a Node/js-yaml version mismatch, or a missing `pymongo`/`pyyaml`/`jinja2`) —
don't hand-edit the generated files to match your template change instead. Hand-syncing risks drifting from what the
generator would actually produce, and that drift can go unnoticed indefinitely. If you can't get regeneration working,
don't make this edit; flag the blocked file to the operator instead of guessing.

## Step 5: Verify Judgment Calls Against Ground Truth

When a proposed simplification claims two conditions are now equivalent (e.g. "not standalone" now implies "supports
sessions" at the new floor), don't reason about it in the abstract — check a real driver implementation. Look for one
checked out as a sibling directory (e.g. `find ~ -maxdepth 3 -iname 'mongo-*-driver' -type d 2>/dev/null`) and grep its
source for the actual field/method involved (e.g. `logical_session_timeout_minutes`, `is_standalone`). If no driver
checkout is available, say so explicitly and flag the simplification as an unverified judgment call for human review
rather than guessing. This is cheap insurance: it caught a plausible-but-wrong simplification (a `change-streams.md`
edit that had to be reverted) before it shipped, and confirmed a reviewer's suggestion should be rejected rather than
accepted (a `retryable-writes.md` "redundant check" claim that turned out to be false — `logicalSessionTimeoutMinutes`
filters out arbiters/non-readable members, which `isStandalone()` alone does not).

## Step 6: Batch, Checkpoint, Commit Incrementally

Report findings grouped by confidence (fix / borderline) before editing anything. Apply fixes in small batches, validate
each batch with `pre-commit run --files <batch>` immediately, and commit with descriptive messages — not one giant diff
at the end. This keeps review and rollback tractable across what is usually a multi-round, multi-day cleanup, and each
content-changing file needs its own `## Changelog` entry per this repo's convention.

For numbered or named prose test lists that other drivers reference by index (e.g. `sessions/tests/README.md`,
`change-streams/tests/README.md`), never delete-and-renumber a dead entry — replace its content with `**Removed**`
instead, so the index stays stable. Plain (unordered) bullet lists have no such constraint and can be deleted outright.

## Step 7: Expect Iteration

Every time a new *shape* of miss turns up (e.g. spelled-out wire version vs. numeric, exact-floor qualifier vs.
below-floor, table cell vs. prose), immediately re-run a repo-wide sweep for that specific new pattern — don't just fix
the one instance found. Treat each new miss as evidence the pattern-net in Step 4 was incomplete, not as an isolated
bug.

## Step 8: Watch for Tooling Side Effects

- `mdformat` may auto-normalize changelog list spacing (loose vs. tight lists) — re-run `pre-commit` a second time after
    the first "files were modified" failure to confirm it settles.
- Comment-only YAML edits don't affect generated JSON — but if `make -C source` is broken locally (e.g. a js-yaml/Node
    version mismatch), verify this explicitly rather than assuming, and flag the tooling gap.

## Delegating to Subagents

Match the model to the task:

- **Mechanical, well-specified batches** (e.g. "remove this exact header line from these N files") → cheap/fast model,
    run in parallel.
- **Exhaustive repo-wide search-and-classify passes** → a stronger model, given the explicit fix/leave criteria from
    Step 2 and instructed to read context around every hit, not just grep and report line matches.
- **Ground-truth verification against a reference driver implementation** → do directly; don't delegate a judgment call
    you can't check yourself.

## Closing Steps

- Update `## Changelog` sections per file touched, following the repo's existing dating/ordering convention.
- Update the PR description and the JIRA ticket description to reflect the *actual final* scope — call out what was
    found beyond the original estimate. Be careful not to mark the ticket "Resolved" while the PR is still awaiting
    approvals; use "In Review" or similar until it's actually merged.
- If squashing commits before merge, verify the rewrite is lossless: confirm the new base is an ancestor of the original
    tip (`git merge-base --is-ancestor <base> <tip>`), then diff the squashed branch against the original tip to confirm
    the resulting tree is identical before pushing.

## Common Mistakes

| Mistake                                                  | Fix                                                      |
| -------------------------------------------------------- | -------------------------------------------------------- |
| Scoping search to already-changed files                  | Always sweep the whole repo, every pass                  |
| Only searching for "below the floor" versions            | Also search for "at the floor" qualifiers — equally dead |
| Classifying from the grep line alone                     | Read 10+ lines of context before deciding fix vs. leave  |
| Assuming a simplification is equivalent without checking | Verify against a real driver implementation              |
| Deleting numbered test entries other drivers reference   | Mark `**Removed**`, keep the index stable                |
| One giant edit at the end                                | Small batches, validated and committed incrementally     |
| Fixing only the one instance of a newly-found miss shape | Re-sweep the whole repo for that pattern immediately     |
| Marking a ticket/PR "Resolved" while still in review     | Reflect actual state until merged                        |
