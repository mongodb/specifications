description = """Generates YAML/JSON tests from a template file.

This keeps key documents, JSONSchemas, and ciphertexts out of the
handwritten test files to make them more readable and easier
to change.
"""


from jinja2 import Template
import yaml
import json
import sys
import os
import bson
from bson import json_util

if sys.version_info < (3, 0):
    print("Use Python 3")
    sys.exit(1)

if len(sys.argv) != 2:
    print(description)
    print("usage: python generate.py /path/to/<filename>.template.yml")
    sys.exit(1)

filepath = sys.argv[1]
filedir = os.path.dirname(filepath)
(filename, ext) = os.path.splitext(os.path.basename(filepath))
if ext != ".yml":
    print("Input file must end with .yml")
    sys.exit(1)
(filename, ext) = os.path.splitext(filename)
if ext != ".template":
    print("Input file must end with .template.yml")
    sys.exit(1)

master_keys = {
    "aws": {
        "provider": "aws",
        "key": "arn:aws:kms:us-east-1:579766882180:key/89fcc2c4-08b0-4bd9-9f25-e30687b580d0",
        "region": "us-east-1"
    },
    "local": {}
}

keys = {
    "basic": {
        "status": 1,
        "_id": {
            "$binary": {
                "base64": "AAAAAAAAAAAAAAAAAAAAAA==",
                "subType": "04"
            }
        },
        "masterKey": master_keys["aws"],
        "updatedDate": {
            "$date": {
                "$numberLong": "1552949630483"
            }
        },
        "keyMaterial": {
            "$binary": {
                "base64": "AQICAHhQNmWG2CzOm1dq3kWLM+iDUZhEqnhJwH9wZVpuZ94A8gEseZD3pQK21IQydtAgPuMjAAAAojCBnwYJKoZIhvcNAQcGoIGRMIGOAgEAMIGIBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDCRqOG6J3KQJ6fZH/AIBEIBbRtAOLl2PRknCve94T9OfEV+sLeE3Jn+Ewtsq1eGuj9Vldxxfq1lFSou7YwZVJyQpx5nZTsUVx3LgCk7B/WY/j4f6FWHteJ63zw6CNMPC5Gi1fubsu1tqwjwRLg==",
                "subType": "00"
            }
        },
        "creationDate": {
            "$date": {
                "$numberLong": "1552949630483"
            }
        }
    },
    "local": {
        "_id": {
            "$binary": {
                "base64": "AAAAAAAAAAAAAAAAAAAAAA==", 
                "subType": "04"
            }
        },
        "keyMaterial": {
            "$binary": {
                "base64": "j8V54E0Yp0nnMI9fxTuUlXcNb496dRHeWvVDs/ESv9Iz3sbbD8mZQ3DUjkIIIgFu9NxiJy7INAI2BW50gpbnbESTD5qj7usHzNYdYTC3rrlWzrE/QZZhI1+q5rUQGjGhXFYwbb3zPuk2KngbuQzle3l6BUyK+SQJ5yD4n/2Sx5E=",
                "subType": "00"
            }
        },
        "creationDate": { "$date": { "$numberLong": "1232739599082000" } },
        "updateDate": { "$date": { "$numberLong": "1232739599082000" } },
        "status": { "$numberInt": "0" },
        "masterKey": { "provider": "local" }
    }
}

schemas = {
    "basic": {
        "properties": {
            "ssn": {
                "encrypt": {
                    "keyId": [keys["basic"]["_id"]],
                    "bsonType": "string",
                    "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic",
                    "initializationVector": {
                        "$binary": {
                            "base64": "aWlpaWlpaWlpaWlpaWlpaQ==",
                            "subType": "00"
                        }
                    }
                }
            },
            "random": {
                "encrypt": {
                    "keyId": [keys["basic"]["_id"]],
                    "bsonType": "string",
                    "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Random",
                }
            }
        },
        "bsonType": "object"
    },
    "local": {
        "properties": {
            "ssn": {
                "encrypt": {
                    "keyId": [keys["local"]["_id"]],
                    "bsonType": "string",
                    "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic",
                    "initializationVector": {
                        "$binary": {
                            "base64": "aWlpaWlpaWlpaWlpaWlpaQ==",
                            "subType": "00"
                        }
                    }
                }
            },
            "randomized": {
                "encrypt": {
                    "keyId": [keys["local"]["_id"]],
                    "bsonType": "string",
                    "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Random",
                }
            }
        },
        "bsonType": "object"
    }
}

ciphertexts = [
    {
        "schema": "basic",
        "field": "ssn",
        "plaintext": "457-55-5462",
        "data": {
            "$binary": {
                "base64": "AQAAAAAAAAAAAAAAAAAAAAACaWlpaWlpaWlpaWlpaWlpaZngC99HenjphHzhJ2/Be2QvqMgm8ZR+ZaLsoUyV1rwcdrAv7jdevtzpndaZDmFcr4vefVrXCssGizpxUtq8p24=",
                "subType": "06"
            }
        }
    },
    {
        "schema": "basic",
        "field": "ssn",
        "plaintext": "123-45-6789",
        "data": {
            "$binary": {
                "base64": "AQAAAAAAAAAAAAAAAAAAAAACaWlpaWlpaWlpaWlpaWlpaQz9fzDR15Wmpcyl9/g8vO1uzwbfeEM53LrLyItCVu+7WcmW8rx8VRF1zlDykXsCL+zm9jRE2+zuhv1ZQwzQlkI=",
                "subType": "06"
            }
        }
    },
    {
        "schema": "local",
        "field": "ssn",
        "plaintext": "457-55-5462",
        "data": {
            "$binary": {
                "base64": "AQAAAAAAAAAAAAAAAAAAAAACaWlpaWlpaWlpaWlpaWlpafBneFKswGbiqdun/OpV9uTCNSocPgh3jCyPOo/2fr4vkPdKsoeZHkeL9UQ+5a+9+V7CaJiLQlE448UCcTppaHU=",
                "subType": "06"
            }
        }
    }
]

def schema(name="basic"):
    return schemas[name]


def key(name="basic"):
    return keys[name]


def ciphertext(plaintext, field, schema="basic"):
    for ciphertext in ciphertexts:
        if schema == ciphertext["schema"] and field == ciphertext["field"] and plaintext == ciphertext["plaintext"]:
            return ciphertext["data"]
    raise Exception("Ciphertext needs to be pre-generated")

def local_provider():
    return {
        "key": {"$binary": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==", "$type": "00"}
    }


template = Template(open(filepath, "r").read())
injections = {
    "schema": schema,
    "ciphertext": ciphertext,
    "key": key,
    "local_provider": local_provider
}

rendered = template.render(**injections)
# check for valid YAML.
parsed = yaml.load(rendered)
# print as JSON.
as_json = json.dumps(parsed, indent=4)
open(f"{os.path.join(filedir,filename + '.yml')}", "w").write(rendered)
open(f"{os.path.join(filedir,filename + '.json')}", "w").write(as_json)
print(f"Generated {os.path.join(filedir,filename)}.yml|json")