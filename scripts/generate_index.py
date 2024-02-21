import os
from pathlib import Path
source = Path(__file__).resolve().parent.parent / "source"
source = source.resolve()
info = {}
for p in Path(source).rglob("*.md"):
    relpath = os.path.relpath(p.parent, start=source)
    if "tests" in relpath:
        continue
    if p.name in ['index.md']:
        continue
    fpath = relpath + '/' + p.name
    name = None
    with p.open() as fid:
        for line in fid:
            if line.startswith("# "):
                name = line.replace('# ', '').strip()
                break
    if name is None:
        raise ValueError(f'Could not find name for {fpath}')
    info[name] = fpath

index_file = source / "index.md"
with index_file.open("w") as fid:
    fid.write('# MongoDB Specifications\n\n')
    for name in sorted(info):
        fid.write(f'- [{name}]({info[name]})\n')