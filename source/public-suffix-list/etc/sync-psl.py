"""Sync the Public Suffix List from publicsuffix.org into this specification.

Usage:

    python source/public-suffix-list/etc/sync-psl.py [--check]

Downloads the upstream list, strips comment and blank lines, and writes the result
to source/public-suffix-list/public_suffix_list.dat. With --check, does not write
anything and exits non-zero if the committed file is out of date.
"""

import argparse
import sys
import urllib.request
from pathlib import Path

PSL_URL = "https://publicsuffix.org/list/public_suffix_list.dat"

# Seconds to wait on the download in a local run.
TIMEOUT_SECONDS = 30

# source/public-suffix-list/etc/sync-psl.py -> source/public-suffix-list
SPEC_DIR = Path(__file__).resolve().parent.parent
DEST = SPEC_DIR / "public_suffix_list.dat"


def fetch():
    request = urllib.request.Request(PSL_URL, headers={"User-Agent": "mongodb-specifications-sync-psl"})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        if not response.url.startswith("https://"):
            sys.exit(f"Refusing to use non-HTTPS response URL {response.url!r}.")

        data = response.read()

    text = data.decode("utf-8")

    # Sanity check: the upstream file always carries these section markers.
    for marker in ("// ===END ICANN DOMAINS===", "// ===END PRIVATE DOMAINS==="):
        if marker not in text:
            sys.exit(f"Downloaded file is missing expected markers {marker!r}; refusing to write.")

    return text


def preprocess(text):
    """Reduce the upstream list to one rule per line.

    Comment lines (those beginning with "//") and blank lines are both removed, so
    every line will be a rule.
    """
    rules = []
    for line in text.splitlines():
        # Upstream rules are not indented, but strip anyway so a stray trailing \r or
        # space does not end up inside a rule.
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        rules.append(line)

    if not rules:
        sys.exit("No rules found after stripping comments; refusing to write.")

    # End the file with exactly one newline.
    return "\n".join(rules) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if the committed list differs from upstream, without writing",
    )
    args = parser.parse_args()

    new_text = preprocess(fetch())

    old_text = DEST.read_text(encoding="utf-8") if DEST.exists() else None

    if args.check:
        if old_text is None:
            sys.exit(f"{DEST} does not exist; run this script without --check.")
        if old_text != new_text:
            sys.exit(f"{DEST} is out of date; run source/public-suffix-list/etc/sync-psl.py.")
        print(f"{DEST.name} is up to date.")
        return

    if old_text == new_text:
        print(f"{DEST.name} is already up to date ({len(new_text.splitlines())} lines).")
        return

    DEST.write_text(new_text, encoding="utf-8")
    print(f"Wrote {DEST} ({len(new_text.splitlines())} lines).")


if __name__ == "__main__":
    main()
