import subprocess
import os
import re
import sys
from pathlib import Path
import datetime

if len(sys.argv) < 2:
    print('Must provide a path to an RST file')
    sys.exit(1)

path = Path(sys.argv[1])

# Get the contents of the file.
with path.open() as fid:
    lines = fid.readlines()


# Pre-process the file.
for (i, line) in enumerate(lines):
    # Replace the colon fence blocks with bullets,
    # e.g. :Status:, :deprecated:, :changed:.
    # This also includes the changelog entries.
    match = re.match(r':(\S+):(.*)', line)
    if match:
        name, value = match.groups()
        lines[i] = f'- {name.capitalize()}:{value}\n'

    # Handle "":Minimum Server Version:"" as a block quote.
    if line.strip().startswith(':Minimum Server Version:'):
        lines[i] = '- ' + line.strip()[1:] + ''


    # Remove the "".. contents::" block - handled by GitHub UI.
    if line.strip() == '.. contents::':
        lines[i] = ''


# Run pandoc and capture output.
proc = subprocess.Popen(['pandoc', '-f', 'rst', '-t', 'gfm'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
data = ''.join(lines).encode('utf8')
outs, _ = proc.communicate(data)
data = outs.decode('utf8')

# Fix the strings that were missing backticks.
data = re.sub(r'<span\W+class="title-ref">', '`', data, flags=re.MULTILINE)
data = data.replace('</span>', '`')

# Handle div blocks that were created.
# These are admonition blocks, convert to new GFM format.
# Also add a changelog entry.
in_block_outer = False
in_block_inner = False
in_changelog_first = False
lines = data.splitlines()
new_lines = []
for (i, line) in enumerate(lines):
    match = re.match(r'<div class="(\S+)">',line)
    if not in_block_outer and match:
        in_block_outer = True
        new_lines.append(f'> [!{match.groups()[0].upper()}]')
        continue
    if line.strip() == '</div>':
        if in_block_outer:
            in_block_outer = False
            in_block_inner = True
        elif in_block_inner:
            in_block_inner = False
        continue
    if in_block_inner:
        line = '> ' + line.strip()

    if in_changelog_first:
        today = datetime.date.today().strftime('%Y-%m-%d')
        line = f'\n- {today}: Migrated from reStructuredText to Markdown.'
        in_changelog_first = False

    if line.strip() == '## Changelog':
        in_changelog_first = True

    if not in_block_outer:
        new_lines.append(line)    


# Write the new content to the markdown file.
md_file = str(path).replace('.rst', '.md')
with open(md_file, 'w') as fid:
    fid.write('\n'.join(new_lines))

# Handle links in other files.
# We accept relative path links or links to master 
# (https://github.com/mongodb/specifications/blob/master/source/...)
# and rewrite them to use appropriate md links.
# If the link is malformed we ignore and print an error.
pattern = re.compile(f'(<.*{path.parent.name}/{path.name}[>#])')
for p in Path("source").rglob("*"):
    if not '.rst' in p.name:
        continue
    found = False
    with p.open() as fid:
        lines = fid.readlines()
    new_lines = []
    for line in lines:
        match = re.search(pattern, line)
        if not match:
            new_lines.append(line)
            continue
        matchstr = match.groups()[0]
        if matchstr[0].startswith('https'):
            if not substr.startswith('<https://github.com/mongodb/specifications/blob/master/source/'):
                print('*** Error in link: ', substr, p)
                new_lines.append(line)
                continue
        found = True
        relpath = os.path.relpath(path.parent.parent, start=p.parent)
        new_name = path.name.replace('.rst', '.md')
        new_substr = f'<{relpath}/{path.parent.name}/{new_name}{matchstr[-1]}'
        new_lines.append(line.replace(matchstr, new_substr))

    if found:
        with p.open('w') as fid:
            fid.writelines(new_lines)
        print(f'Update link(s) in {p.name}')



print('Created markdown file:')
print(md_file)
