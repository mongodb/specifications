import subprocess
import re
import sys

if len(sys.argv) < 2:
    print('Must provide a path to an RST file')
    sys.exit(1)

path = sys.argv[1]

# Get the contents of the file.
with open(path) as fid:
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
in_block_outer = False
in_block_inner = False
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
    if not in_block_outer:
        new_lines.append(line)

# Write the new content to the markdown file.
md_file = path.replace('.rst', '.md')
with open(md_file, 'w') as fid:
    fid.write('\n'.join(new_lines))

print('Created markdown file:')
print(md_file)
