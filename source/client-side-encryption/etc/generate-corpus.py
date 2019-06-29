
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
schema_fields = []
corpus = []

def prohibited(map):
    if map["type"] in ["undefined", "minKey", "maxKey", "null"]:
        return True
    if map["type"] in ["object", "array", "double", "decimal", "javascriptWithScope", "javascript", "bool"]  and map["algo"] == "det":
        return True
    return False

def gen_schema (map):
    fmt = """"%s": { "encrypt": { "keyId": %s, "algorithm": "%s", "bsonType": "%s" } }"""
    field_name = map["kms"] + "_" + map["type"] + "_" + map["algo"] + "_" + map["method"] + "_" + map["identifier"]

    if map["method"] == "explicit":
        return """"%s": { "bsonType": "binData" }""" % field_name

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
            
    return fmt % (field_name, key_id, algorithm, type)

def get_bson_value (bson_type):
    if bson_type == "double":
        return """{ "$numberDouble" : 1.234 }"""
    if bson_type == "string":
        return """ "mongodb" """
    if bson_type == "object":
        return """ { "x" : { "$numberInt": 1 } } """
    if bson_type == "array":
        return """ [ { "$numberInt": 1 }, { "$numberInt": 2 }, { "$numberInt": 3 } ] """
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
        return """ { "$ref": "db.example", "$id": { "$oid": "01234567890abcdef0123456" } } """
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

def gen_field (map):
    field_name = map["kms"] + "_" + map["type"] + "_" + map["algo"] + "_" + map["method"] + "_" + map["identifier"]

    bson_value = get_bson_value (map["type"])
    return """ "%s" : %s """ % (field_name, bson_value)

def enumerate_axis (map, axis, remaining):
    name = axis[0]
    for item in axis[1]:
        map[name] = item
        if remaining == []:
            is_prohibited = prohibited(map)
            # for prohibited mappings, only allow explicit, replace it with prohibited.
            if is_prohibited:
                if map["method"] == "explicit":
                    map["method"] = "prohibited"
                else:
                    continue
                
            if not is_prohibited:
                schema_fields.append(gen_schema(map))

            corpus.append(gen_field(map))
        else:
            enumerate_axis (map, remaining[0], remaining[1:])

enumerate_axis({}, axes[0], axes[1:])

schema = """{ "bsonType": "object", "properties": { %s } }""" % (",\n".join(schema_fields))
open("schema.json", "w").write(schema)
open("corpus.json", "w").write("{%s}" % ",\n".join(corpus))