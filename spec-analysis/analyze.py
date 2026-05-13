#!/usr/bin/env python3
"""
Analyze MongoDB spec components and generate analysis reports in spec-analysis/.

Usage:
    python spec-analysis/analyze.py <component> [<component> ...]
    python spec-analysis/analyze.py --all
    python spec-analysis/analyze.py --tier3
    python spec-analysis/analyze.py --tier4

Examples:
    python spec-analysis/analyze.py crud retryable-reads
    python spec-analysis/analyze.py --tier3
"""
import argparse
import os
import sys
from pathlib import Path

import anthropic

REPO_ROOT = Path(__file__).parent.parent
SPEC_DIR = REPO_ROOT / "source"
OUTPUT_DIR = REPO_ROOT / "spec-analysis"

TIERS = {
    3: [
        "max-staleness",
        "client-side-operations-timeout",
        "command-logging-and-monitoring",
        "open-telemetry",
        "retryable-writes",
        "connection-monitoring-and-pooling",
    ],
    4: [
        "retryable-reads",
        "transactions",
        "initial-dns-seedlist-discovery",
        "server-selection",
        "client-side-encryption",
        "server-discovery-and-monitoring",
        "crud",
        "unified-test-format",
    ],
}

PROMPT_TEMPLATE = """You are analyzing a MongoDB driver specification component to identify gaps and issues.

## Component: {component}

## Spec file content:
{spec_content}

## Existing test files:
{test_listing}

## Sample test content (first 3 files):
{test_samples}

---

Produce a concise analysis report in the following Markdown format:

# Analysis: {component}

## Missing Tests
- [ ] <behavior from spec (cite section)> — <what test would verify>
(List behaviors described with MUST/MUST NOT/SHALL/SHOULD that have NO corresponding test coverage.
Prose tests in the spec itself count as coverage only if they are numbered and well-defined.)

## Ambiguities
- <section name or short quote>: <description of the vague/undefined behavior and suggested clarification>

## Inconsistencies
- <description of the contradiction, with references to spec section and/or test file names>

## Notes
- <other observations: missing Changelog, RST duplicates, infrastructure requirements, etc.>

Rules:
- Be specific: cite section names or line ranges when possible.
- Cross-reference: for each MUST/SHOULD, check if an existing test file exercises it.
- Keep each bullet concise (one line).
- If a section is empty (no issues found), write "None identified."
"""


def find_spec_file(component: str) -> Path | None:
    """Find the main .md spec file for a component."""
    comp_dir = SPEC_DIR / component
    if not comp_dir.is_dir():
        return None
    # Try exact name match first, then any .md
    candidates = [
        comp_dir / f"{component}.md",
        comp_dir / f"{component.replace('-', '_')}.md",
    ]
    for c in candidates:
        if c.exists():
            return c
    md_files = [f for f in comp_dir.glob("*.md") if f.name != "README.md"]
    return md_files[0] if md_files else None


def collect_tests(component: str) -> tuple[list[Path], str]:
    """Return list of YAML test files and a string listing them."""
    tests_dir = SPEC_DIR / component / "tests"
    if not tests_dir.is_dir():
        return [], "No tests/ directory."
    yaml_files = sorted(tests_dir.rglob("*.yml")) + sorted(tests_dir.rglob("*.yaml"))
    if not yaml_files:
        return [], "tests/ directory exists but contains no YAML files."
    listing = f"{len(yaml_files)} YAML test files:\n" + "\n".join(
        f"  - {f.relative_to(SPEC_DIR / component)}" for f in yaml_files[:40]
    )
    if len(yaml_files) > 40:
        listing += f"\n  ... and {len(yaml_files) - 40} more"
    return yaml_files, listing


def sample_tests(yaml_files: list[Path], n: int = 3) -> str:
    """Return the content of the first n test files (truncated)."""
    if not yaml_files:
        return "No test files."
    samples = []
    for f in yaml_files[:n]:
        content = f.read_text(encoding="utf-8")[:3000]
        samples.append(f"### {f.name}\n```yaml\n{content}\n```")
    return "\n\n".join(samples)


def analyze_component(component: str, client: anthropic.Anthropic) -> str:
    """Call the Claude API to analyze a single component."""
    spec_file = find_spec_file(component)
    if spec_file is None:
        return f"# Analysis: {component}\n\n> **ERROR**: No spec file found in `source/{component}/`.\n"

    spec_content = spec_file.read_text(encoding="utf-8")
    # Truncate very large specs to fit in context
    if len(spec_content) > 80_000:
        spec_content = spec_content[:80_000] + "\n\n[...truncated for length...]"

    yaml_files, test_listing = collect_tests(component)
    test_samples = sample_tests(yaml_files)

    prompt = PROMPT_TEMPLATE.format(
        component=component,
        spec_content=spec_content,
        test_listing=test_listing,
        test_samples=test_samples,
    )

    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze MongoDB spec components.")
    parser.add_argument("components", nargs="*", help="Component names to analyze")
    parser.add_argument("--all", action="store_true", help="Analyze all tier 3+4 components")
    parser.add_argument("--tier3", action="store_true", help="Analyze tier 3 components")
    parser.add_argument("--tier4", action="store_true", help="Analyze tier 4 components")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing reports")
    args = parser.parse_args()

    components: list[str] = list(args.components)
    if args.all or args.tier3:
        components += TIERS[3]
    if args.all or args.tier4:
        components += TIERS[4]

    if not components:
        parser.print_help()
        sys.exit(1)

    # Deduplicate while preserving order
    seen: set[str] = set()
    components = [c for c in components if not (c in seen or seen.add(c))]

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    OUTPUT_DIR.mkdir(exist_ok=True)

    for component in components:
        out_file = OUTPUT_DIR / f"{component}.md"
        if out_file.exists() and not args.overwrite:
            print(f"  SKIP  {component} (report already exists; use --overwrite to replace)")
            continue

        print(f"  ...   {component}", end="", flush=True)
        try:
            report = analyze_component(component, client)
            out_file.write_text(report + "\n", encoding="utf-8")
            print(f"\r  DONE  {component} → spec-analysis/{component}.md")
        except Exception as exc:
            print(f"\r  FAIL  {component}: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
