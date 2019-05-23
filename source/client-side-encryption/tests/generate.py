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
        "updateDate": {
            "$date": {
                "$numberLong": "1552949630483"
            }
        },
        "keyMaterial": {
            "$binary": {
                "base64": "AQICAHhQNmWG2CzOm1dq3kWLM+iDUZhEqnhJwH9wZVpuZ94A8gF9FSYZL9Ze8TvTA3WBd3nmAAAAwjCBvwYJKoZIhvcNAQcGoIGxMIGuAgEAMIGoBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDLV3GHktEO8AlpsYBwIBEIB7ho0DQF7hEQPRz/8b61AHm2czX53Y9BNu5z+oyGYsoP643M58aTGsaHQzkTaAmGKlZTAEOjJkRJ4gZoabVuv4g6aJqf4k4w8pK7iIgHwMNy4nbUAqOWmqtnKpHZgy6jcFN2DzZzHIi4SNFsCkFc6Aw30ixtvqIDQPAXMW",
                "subType": "00"
            }
        },
        "creationDate": {
            "$date": {
                "$numberLong": "1552949630483"
            }
        },
        "keyAltNames": ["altname", "another_altname"]
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
                "base64": "db27rshiqK4Jqhb2xnwK4RfdFb9JuKeUe6xt5aYQF4o62tS75b7B4wxVN499gND9UVLUbpVKoyUoaZAeA895OENP335b8n8OwchcTFqS44t+P3zmhteYUQLIWQXaIgon7gEgLeJbaDHmSXS6/7NbfDDFlB37N7BP/2hx1yCOTN6NG/8M1ppw3LYT3CfP6EfXVEttDYtPbJpbb7nBVlxD7w==",
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
            "encrypted_w_altname": {
                "encrypt": {
                    "keyId": "/altname",
                    "bsonType": "string",
                    "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic"
                }
            },
            "ssn": {
                "encrypt": {
                    "keyId": [keys["basic"]["_id"]],
                    "bsonType": "string",
                    "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic"
                }
            },
            "random": {
                "encrypt": {
                    "keyId": [keys["basic"]["_id"]],
                    "bsonType": "string",
                    "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Random",
                }
            },
            # Same exact as fields as "ssn"
            "ssn_equivalent": {
                "encrypt": {
                    "keyId": [keys["basic"]["_id"]],
                    "bsonType": "string",
                    "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic"
                }
            }
        },
        "bsonType": "object"
    },
    "encrypted_id": {
        "properties": {
            "_id": {
                "encrypt": {
                    "keyId": [keys["basic"]["_id"]],
                    "bsonType": "string",
                    "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic"
                }
            }
        }
    },
    "local": {
        "properties": {
            "ssn": {
                "encrypt": {
                    "keyId": [keys["local"]["_id"]],
                    "bsonType": "string",
                    "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic"
                }
            },
            "random": {
                "encrypt": {
                    "keyId": [keys["local"]["_id"]],
                    "bsonType": "string",
                    "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Random",
                }
            }
        },
        "bsonType": "object"
    },
    "invalid_array": {
        "properties": {
            "ssn": {
                "encrypt": {
                    "keyId": [keys["basic"]["_id"]],
                    "bsonType": "string",
                    "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Random"
                }
            }
        },
        "bsonType": "array"
    },
    "invalid_omitted_type": {
	    "properties": {
            "foo": {
                "properties": {
                    "bar": {
                        "encrypt": {
                            "keyId": [keys["basic"]["_id"]],
                            "bsonType": "string",
                            "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Random"
                        }
                    }
                }
            }
        }
    },
    "invalid_siblings": {
        "properties": {
            "ssn": {
                "encrypt": {
                    "keyId": [keys["basic"]["_id"]],
                    "bsonType": "string",
                    "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Random"
                },
                "bsonType": "object"
            }
        }
    },
    "logical_keywords": {
        "anyOf": [
            {
                "properties": {
                    "ssn": {
                        "encrypt": {
                            "keyId": [keys["basic"]["_id"]],
                            "bsonType": "string",
                            "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Random"
                        }
                    }
                }
            }
        ]
    }
}

ciphertexts = [
    {
        "schema": "basic",
        "field": "ssn",
        "plaintext": "457-55-5462",
        "data": {
            "$binary": {
                "base64": "AQAAAAAAAAAAAAAAAAAAAAACsdNMtVDy09S7BbEGrxNeFPKWl/7qb2EFqJfA2FqBEK1jW/5WFUZTPKWls9PBz+4Ro8Z6g5b+zAY+rh0bHmssKfg4g3GZ3j7rBt1tyqh3B2w=",
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
                "base64": "AQAAAAAAAAAAAAAAAAAAAAACUMZIlZ4eQzJmNxnxOi5fqWrhnpXDXdOPdkRG4hbqOTmTIN2+WfGXTcAaszTRg7XhM01c18lfd3XtPl3iUNXU6fEYjGf1mLPkQ3tlO3wOf/k=",
                "subType": "06"
            }
        }
    },
    {
        "schema": "basic",
        "field": "ssn",
        "plaintext": "987-65-4321",
        "data": {
            "$binary": {
                "base64": "AQAAAAAAAAAAAAAAAAAAAAACzcsm4xHv+De4+H3IDRaSJEx1f3Qs19qdophSh+XsQpYMcgo64MeiAP00umr3s7DTSy7mzuSRLZ/iuqxbNdThgp5KQvNB8kWrLnB+Zk0qom8",
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
                "base64": "AQAAAAAAAAAAAAAAAAAAAAACNnpgkgV4PUCayKHJ/K8Qb6nM9Z71cn91//1gC+j7Wsxaow8haaNU5aYlOAeyu+7Akke/QuHb0AqtQa1meuGeDDDUyPCC8xgNwAIh3A1tdbs=",
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
        "key": {"$binary": { "base64": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "subType": "00"}  }
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