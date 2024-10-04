
"""
A utility script written to generate the limits schema and data.
"""
from pymongo import MongoClient
from bson import json_util
import bson
from bson.son import SON
from bson.codec_options import CodecOptions
import base64


codec_options = CodecOptions(uuid_representation=bson.binary.STANDARD)
json_options = json_util.JSONOptions(json_mode=json_util.JSONMode.CANONICAL, uuid_representation=bson.binary.STANDARD)
schema = SON()
doc = SON()

for i in range(100):
    key = "%02d" % i
    doc[key] = "a"
    schema[key] = {
        "encrypt": {
            "keyId": [bson.Binary(base64.b64decode("LOCALAAAAAAAAAAAAAAAAA=="), bson.binary.UUID_SUBTYPE)],
            "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic",
            "bsonType": "string"
        }
    }

open("limits-doc.json", "w").write(json_util.dumps(doc, json_options=json_options, indent=4))
open("limits-schema.json", "w").write(json_util.dumps({"bsonType": "object", "properties": schema}, json_options=json_options, indent=4))