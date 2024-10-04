import json
import sys
import os

description = """Generates the data and JSON Schema for the corpus test in the target directory.
"""

if len(sys.argv) != 2:
    print(description)
    print("usage: python generate-corpus.py <target directory>")
    print("example: python ./generate-corpus.py ./")
    sys.exit(1)

targetdir = sys.argv[1]

# Generate test data from this matrix of axes.
axes = [
    ("kms", [ "aws", "local", "azure", "gcp", "kmip"]),
    ("type", [ "double", "string", "object", "array", "binData=00", "binData=04", "undefined", "objectId", "bool", "date", "null", "regex", "dbPointer", "javascript", "symbol", "javascriptWithScope", "int", "timestamp", "long", "decimal", "minKey", "maxKey" ]),
    ("algo", [ "rand", "det" ]),
    ("method", [ "auto", "explicit" ]),
    ("identifier", [ "id", "altname" ])
]

def allowed(map):
    if map["type"] in ["undefined", "minKey", "maxKey", "null"]:
        return False
    if map["type"] in ["object", "array", "double", "decimal", "javascriptWithScope", "bool"]  and map["algo"] == "det":
        return False
    if map["algo"] == "det" and map["identifier"] == "altname" and map["method"] == "auto":
        # prohibited per SERVER-42010
        return False
    return True

def gen_schema (map):
    fmt = """ { "bsonType": "object", "properties": { "value": { "encrypt": { "keyId": %s, "algorithm": "%s", "bsonType": "%s" } } } } """

    if not allowed(map):
        # We cannot even set a schema, don't test auto with prohibited fields.
        return None

    if map["method"] == "explicit":
        return """ { "bsonType": "object", "properties": { "value": { "bsonType": "binData" } } } """ 

    if map["identifier"] == "id":
        if map["kms"] == "local":
            key_id = """[ { "$binary": { "base64": "LOCALAAAAAAAAAAAAAAAAA==", "subType": "04" } } ]"""
        elif map["kms"] == "aws":
            key_id = """[ { "$binary": { "base64": "AWSAAAAAAAAAAAAAAAAAAA==", "subType": "04" } } ]"""
        elif map["kms"] == "azure":
            key_id = """[ { "$binary": { "base64": "AZUREAAAAAAAAAAAAAAAAA==", "subType": "04" } } ]"""
        elif map["kms"] == "gcp":
            key_id = """[ { "$binary": { "base64": "GCPAAAAAAAAAAAAAAAAAAA==", "subType": "04" } } ]"""
        elif map["kms"] == "kmip":
            key_id = """[ { "$binary": { "base64": "KMIPAAAAAAAAAAAAAAAAAA==", "subType": "04" } } ]"""
    else:
        key_id = "\"/altname_" + map["kms"] + "\""

    if map["algo"] == "rand":
        algorithm = "AEAD_AES_256_CBC_HMAC_SHA_512-Random"
    else:
        algorithm = "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic"

    type = map["type"]
    if map["type"].startswith("binData"):
        type = "binData"
    
    return fmt % (key_id, algorithm, type)

def get_bson_value (bson_type):
    if bson_type == "double":
        return """{ "$numberDouble" : "1.234" }"""
    if bson_type == "string":
        return """ "mongodb" """
    if bson_type == "object":
        return """ { "x" : { "$numberInt": "1" } } """
    if bson_type == "array":
        return """ [ { "$numberInt": "1" }, { "$numberInt": "2" }, { "$numberInt": "3" } ] """
    if bson_type == "binData=00":
        return """ { "$binary": { "base64": "AQIDBA==", "subType": "00" } } """
    if bson_type == "binData=04":
        return """ { "$binary": { "base64": "AAECAwQFBgcICQoLDA0ODw==", "subType": "04" } }"""
    if bson_type == "objectId":
        return """ { "$oid": "01234567890abcdef0123456" } """
    if bson_type == "bool":
        return """ true """
    if bson_type == "date":
        return """ { "$date": { "$numberLong": "12345" } } """
    if bson_type == "regex":
        return """ { "$regularExpression": { "pattern": ".*", "options": "" } } """
    if bson_type == "dbPointer":
        return """ { "$dbPointer": { "$ref": "db.example", "$id": { "$oid": "01234567890abcdef0123456" } } } """
    if bson_type == "javascript":
        return """ { "$code": "x=1" } """
    if bson_type == "javascriptWithScope":
        return """ { "$code": "x=1", "$scope": {} } """
    if bson_type == "symbol":
        return """ { "$symbol": "mongodb-symbol" } """
    if bson_type == "int":
        return """ { "$numberInt": "123" } """
    if bson_type == "timestamp":
        return """ { "$timestamp": { "t": 0, "i": 12345 } } """
    if bson_type == "long":
        return """ { "$numberLong": "456" } """
    if bson_type == "decimal":
        return """ { "$numberDecimal": "1.234" } """
    if bson_type == "undefined":
        return """ {"$undefined": true} """
    if bson_type == "null":
        return "null"
    if bson_type == "minKey":
        return """{"$minKey": 1}"""
    if bson_type == "maxKey":
        return """{"$maxKey": 1}"""

def field_name(map):
    return "%s_%s_%s_%s_%s" % (map["kms"], map["type"], map["algo"], map["method"], map["identifier"])

def gen_field (map):
    if not allowed(map) and map["method"] == "auto":
        # We cannot even set a schema, don't test auto with prohibited fields.
        return None
    allow = "true" if allowed(map) else "false"
    return """ { "kms": "%s", "type": "%s", "algo": "%s", "method": "%s", "identifier": "%s", "allowed": %s, "value": %s }""" % (map["kms"], map["type"], map["algo"], map["method"], map["identifier"], allow, get_bson_value (map["type"]))

schema_sections = []
corpus_sections = [
    """ "_id": "client_side_encryption_corpus" """ ,
    """ "altname_aws": "aws" """ ,
    """ "altname_local": "local" """ ,
    """ "altname_azure": "azure" """ ,
    """ "altname_gcp": "gcp" """ ,
    """ "altname_kmip": "kmip" """ ,
]

def enumerate_axis (map, axis, remaining):
    name = axis[0]
    for item in axis[1]:
        map[name] = item
        if remaining == []:
            key = field_name (map)
            schema_section = gen_schema (map)
            corpus_section = gen_field (map)
            if schema_section:
                schema_sections.append(""" "%s": %s """ % (key, schema_section))
            if corpus_section:
                corpus_sections.append(""" "%s": %s """ % (key, corpus_section))
        else:
            enumerate_axis (map, remaining[0], remaining[1:])

enumerate_axis({}, axes[0], axes[1:])

# Add padding cases
for algo in ("rand", "det"):
    for i in range(17):
        key = "payload=%d,algo=%s" % (i, algo)
        map = {
            "kms": "local",
            "type": "string",
            "algo": algo,
            "method": "explicit",
            "identifier": "id",
            "allowed": True,
            "value": "a" * i
        }
        corpus_sections.append (""" "%s": %s """ % (key, json.dumps(map)))


def reformat (json_str):
    as_json = json.loads(json_str)
    return json.dumps (as_json, indent=2)

schema = """{ "bsonType": "object", "properties": { %s } }""" % (",\n".join(schema_sections))
open(os.path.join(targetdir, "corpus-schema.json"), "w").write(reformat(schema))
corpus = "{%s}" %  ",\n".join(corpus_sections)
open(os.path.join(targetdir, "corpus.json"), "w").write(reformat(corpus))
print("Generated corpus.json and corpus-schema.json in target directory")