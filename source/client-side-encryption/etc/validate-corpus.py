import json
import sys

description = """Validate that the same deterministically encrypted values in the corpus encrypt to the same ciphertext in the encrypted corpus.
"""

if len(sys.argv) != 3:
    print(description)
    print("usage: python validate-corpus.py <corpus.json> <corpus-encrypted.json>")
    sys.exit(1)

corpus = json.loads(open(sys.argv[1], "r").read())
corpus_encrypted = json.loads(open(sys.argv[2], "r").read())

# Get all deterministically encrypted fields that have the same value + kms + type
def get_matching_fields (item):
    for (key, val) in corpus.items():
        if key == "_id" or key == "altname_aws" or key == "altname_local":
            continue
        if val["value"] == item["value"] and val["algo"] == "det" and item["algo"] == val["algo"] and val["kms"] == item["kms"] and val["type"] == item["type"]:
            yield key
    
count = 0
for (key, val) in corpus.items():
    if key == "_id" or key == "altname_aws" or key == "altname_local":
        continue
    for matching_field in get_matching_fields (val):
        count += 1
        if matching_field == key:
            continue
        if corpus_encrypted[matching_field]["value"] != corpus_encrypted[key]["value"]:
            print ("error: %s does not match %s" % (matching_field, key))
            sys.exit(1)

print("validated that %d ciphertexts are exact matches" % count)