import sys, re

fname = sys.argv[-1]

# Roughly detect fenced code even inside block quotes
fenced_code = re.compile(r"^\s*(>\s+)*```")

# Check for markdown links that got improperly line wrapped.
in_code_block = False
with open(fname) as fid:
    for line in fid:
        # Ignore code blocks.
        if fenced_code.match(line):
            in_code_block = not in_code_block
        if in_code_block:
            continue
        id0 = line.index("[") if "[" in line else -1
        id1 = line.index("]") if "]" in line else -1
        id2 = line.index("(") if "(" in line else -1
        id3 = line.index(")") if ")" in line else -1
        if id1 == -1 or id2 == -1 or id3 == -1:
            continue
        if id2 < id1 or id3 < id2:
            continue
        if id0 == -1:
            print("*** Malformed link in line:", line, fname)
            sys.exit(1)

assert not in_code_block
