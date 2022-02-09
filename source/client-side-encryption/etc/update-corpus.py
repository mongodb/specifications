import json
import sys

description = """Update the existing corpus data from a file with only deterministically encrypted fields.
"""

if len(sys.argv) != 3:
    print(description)
    print("usage: python update-corpus.py <new-corpus-data.json> <old-corpus-data.json>")
    print("Updates the deterministic fields of <old-corpus-data.json> in place.")
    sys.exit(1)

new_corpus_path = sys.argv[1]
old_corpus_path = sys.argv[2]
new_corpus_data = json.loads(open(new_corpus_path, "r").read())
old_corpus_data = json.loads(open(old_corpus_path, "r").read())

for (key, val) in new_corpus_data.items():
    if key in ["_id", "altname_aws", "altname_local", "altname_azure", "altname_gcp", "altname_kmip"]:
        continue
    if new_corpus_data[key]["algo"] == "det":
        old_corpus_data[key] = new_corpus_data[key]
    # add random field if it did not exist
    if new_corpus_data[key]["algo"] == "rand" and key not in old_corpus_data:
        old_corpus_data[key] = new_corpus_data[key]

open(old_corpus_path, "w").write(json.dumps(old_corpus_data, indent=2))
print ("updated %s" % (old_corpus_path))
