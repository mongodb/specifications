
"""
A utility script written to generate the corpus data and schema.
"""
from pymongo import MongoClient
from bson import json_util
import bson 
from bson.codec_options import CodecOptions

# Generate test data from this matrix of axes.
axes = [
    ("kms", [ "aws", "local" ]),
    ("type", [ "double", "string", "object", "array", "binData=00", "binData=04", "undefined", "objectId", "bool", "date", "null", "regex", "dbPointer", "javascript", "symbol", "javascriptWithScope", "int", "timestamp", "long", "decimal", "minKey", "maxKey" ]),
    ("algo", [ "rand", "det" ]),
    ("method", [ "auto", "explicit" ]),
    ("identifier", [ "id", "altname" ])
]

codec_options = CodecOptions(uuid_representation=bson.binary.STANDARD)
json_options = json_util.JSONOptions(json_mode=json_util.JSONMode.CANONICAL, uuid_representation=bson.binary.STANDARD)

def allowed(map):
    if map["type"] in ["undefined", "minKey", "maxKey", "null"]:
        return False
    if map["type"] in ["object", "array", "double", "decimal", "javascriptWithScope", "bool"]  and map["algo"] == "det":
        return False
    return True

def gen_schema (map):
    fmt = """ "%s" : { "bsonType": "object", "properties": { "value": { "encrypt": { "keyId": %s, "algorithm": "%s", "bsonType": "%s" } } } } """

    if not allowed(map):
        # We cannot even set a schema, don't test auto with prohibited fields.
        return None

    if map["method"] == "explicit":
        return """ "%s" : { "bsonType": "object", "properties": { "value": { "bsonType": "binData" } } } """ % field_name(map)

    if map["identifier"] == "id":
        if map["kms"] == "local":
            key_id = """[ { "$binary": { "base64": "LOCALAAAAAAAAAAAAAAAAA==", "subType": "04" } } ]"""
        else:
            key_id = """[ { "$binary": { "base64": "AWSAAAAAAAAAAAAAAAAAAA==", "subType": "04" } } ]"""
    else:
        if map["kms"] == "local":
            key_id = "\"/altname_local\""
        else:
            key_id = "\"/altname_aws\""

    if map["algo"] == "rand":
        algorithm = "AEAD_AES_256_CBC_HMAC_SHA_512-Random"
    else:
        algorithm = "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic"

    type = map["type"]
    if map["type"].startswith("binData"):
        type = "binData"
    
    return fmt % (field_name(map), key_id, algorithm, type)

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
    return """ "%s" : { "kms": "%s", "type": "%s", "algo": "%s", "method": "%s", "identifier": "%s", "allowed": %s, "value": %s }""" % (field_name(map), map["kms"], map["type"], map["algo"], map["method"], map["identifier"], allow, get_bson_value (map["type"]))

schema_sections = []
corpus_sections = [
    """ "_id": "client_side_encryption_corpus" """ ,
    """ "altname_aws": "aws" """ ,
    """ "altname_local": "local" """ ,
]

def enumerate_axis (map, axis, remaining):
    name = axis[0]
    for item in axis[1]:
        map[name] = item
        if remaining == []:
            schema_section = gen_schema (map)
            corpus_section = gen_field (map)
            if schema_section:
                schema_sections.append(schema_section)
            if corpus_section:
                corpus_sections.append(corpus_section)
        else:
            enumerate_axis (map, remaining[0], remaining[1:])

enumerate_axis({}, axes[0], axes[1:])

schema = """{ "bsonType": "object", "properties": { %s } }""" % (",\n".join(schema_sections))
open("corpus-schema.json", "w").write(schema)
open("corpus.json", "w").write("{%s}" % ",\n".join(corpus_sections))