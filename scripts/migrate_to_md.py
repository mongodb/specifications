import subprocess
import os
import re
import sys
from pathlib import Path
import datetime
import subprocess

if len(sys.argv) < 2:
    print('Must provide a path to an RST file')
    sys.exit(1)

path = Path(sys.argv[1])

# Ensure git history for the md file.
md_file = str(path).replace('.rst', '.md')
subprocess.check_call(['git', 'mv', path, md_file])
subprocess.check_call(['git', 'add', md_file])
subprocess.check_call(['git', 'commit', '--no-verify', '-m', f'Rename {path} to {md_file}'])
subprocess.check_call(['git', 'checkout', 'HEAD~1', path])
subprocess.check_call(['git', 'add', path])

# Get the contents of the file.
with path.open() as fid:
    lines = fid.readlines()

TEMPLATE = """
.. note::
  This specification has been converted to Markdown and renamed to
  `{0} <{0}>`_.  
"""

# Update the RST file with a stub pointer to the MD file.
if not path.name == 'README.rst':
    new_body = TEMPLATE.format(os.path.basename(md_file))
    with path.open('w') as fid:
        fid.write(''.join(new_body))

# Pre-process the file.
for (i, line) in enumerate(lines):
    # Replace curly quotes with regular quotes.
    line = line.replace('”', '"')
    line = line.replace('“', '"')
    line = line.replace('’', "'")
    line = line.replace('‘', "'")
    lines[i] = line

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
with open(md_file, 'w') as fid:
    fid.write('\n'.join(new_lines))

# Handle links in other files.
# We accept relative path links or links to master 
# (https://github.com/mongodb/specifications/blob/master/source/...)
# and rewrite them to use appropriate md links.
# If the link is malformed we ignore and print an error.
target = path.name
curr = path
while curr.parent.name != 'source':
    target = f'{curr.parent.name}/{target}'
    curr = curr.parent
suffix = fr'\S*/{target}'
rel_pattern = re.compile(fr'(\.\.{suffix})')
md_pattern = re.compile(fr'(\(http{suffix})')
html_pattern = re.compile(f'(http{suffix})')
abs_pattern = re.compile(f'(/source{suffix})')
for p in Path("source").rglob("*"):
    if p.suffix not in ['.rst', '.md']:
        continue
    with p.open() as fid:
        lines = fid.readlines()
    new_lines = []
    changed_lines = []
    relpath = os.path.relpath(md_file, start=p.parent)
    for line in lines:
        new_line = line
        if re.search(rel_pattern, line):
            matchstr = re.search(rel_pattern, line).groups()[0]
            new_line = line.replace(matchstr, relpath)
        elif re.search(md_pattern, line):
            matchstr = re.search(md_pattern, line).groups()[0]
            if not matchstr.startswith('(https://github.com/mongodb/specifications/blob/master/source'):
                print('*** Error in link: ', matchstr, p)
            else:
                new_line = line.replace(matchstr, f'({relpath}')
        elif re.search(html_pattern, line):
            matchstr = re.search(html_pattern, line).groups()[0]
            if not matchstr.startswith('https://github.com/mongodb/specifications/blob/master/source'):
                print('*** Error in link: ', matchstr, p)
            else:
                new_line = line.replace(matchstr, f'{relpath}')
        elif re.search(abs_pattern, line):
            matchstr = re.search(abs_pattern, line).groups()[0]
            new_line = line.replace(matchstr, relpath)

        if new_line != line:
            changed_lines.append(new_line)
        new_lines.append(new_line)

    if changed_lines:
        with p.open('w') as fid:
            fid.writelines(new_lines)
        print('-' * 80)
        print(f'Updated link(s) in {p}...')
        print('    ' + '\n   '.join(changed_lines))

print('Created markdown file:')
print(md_file)
