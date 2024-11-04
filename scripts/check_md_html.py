import sys, re

fname = sys.argv[-1]

# Check for allowed HTML elements in markdown.
# Ignores inline and fenced code, but intentionally doesn't ignore backslash
# escaping. (For compatibility, we want to avoid unintentional inline HTML
# even on markdown implementations where "\<" escapes are not supported.)

disallowed_re = re.compile(
    r"""
    [^`]*(`[^`]+`)*
    <(?!
        - |
        /p> |
        /span> |
        /sub> |
        /sup> |
        /table> |
        /td> |
        /tr> |
        \d |
        \s |
        \w+@(\w+\.)+\w+> | # Cover email addresses in license files
        = |
        br> |
        https:// |         # Cover HTTPS links but not HTTP
        p> |
        span[\s>] |
        sub> |
        sup> |
        table[\s>] |
        td[\s>] |
        tr> |
        !-- )
""",
    re.VERBOSE,
)

# Roughly detect fenced code even inside block quotes
fenced_code = re.compile(r"^\s*(>\s+)*```")

in_code_block = False
with open(fname) as fid:
    for line in fid:
        # Ignore code blocks.
        if fenced_code.match(line):
            in_code_block = not in_code_block
        if in_code_block:
            continue
        if disallowed_re.match(line):
            print("*** Markdown contains unexpected HTML in line:", line, fname)
            sys.exit(1)

assert not in_code_block
