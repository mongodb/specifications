import bson
import os
import sys
import yaml
from jinja2 import Template
from pathlib import Path
description = """Generates YAML/JSON tests from a template file.

This keeps key documents, JSONSchemas, and ciphertexts out of the
handwritten test files to make them more readable and easier
to change.
"""

keys = {
    "basic": {
        "status": 1,
        "_id": {
            "$binary": {
                "base64": "AAAAAAAAAAAAAAAAAAAAAA==",
                "subType": "04"
            }
        },
        "masterKey": {
            "provider": "aws",
            "key": "arn:aws:kms:us-east-1:579766882180:key/89fcc2c4-08b0-4bd9-9f25-e30687b580d0",
            "region": "us-east-1"
        },
        "updateDate": {
            "$date": {
                "$numberLong": "1552949630483"
            }
        },
        "keyMaterial": {
            "$binary": {
                "base64": "AQICAHhQNmWG2CzOm1dq3kWLM+iDUZhEqnhJwH9wZVpuZ94A8gEqnsxXlR51T5EbEVezUqqKAAAAwjCBvwYJKoZIhvcNAQcGoIGxMIGuAgEAMIGoBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDHa4jo6yp0Z18KgbUgIBEIB74sKxWtV8/YHje5lv5THTl0HIbhSwM6EqRlmBiFFatmEWaeMk4tO4xBX65eq670I5TWPSLMzpp8ncGHMmvHqRajNBnmFtbYxN3E3/WjxmdbOOe+OXpnGJPcGsftc7cB2shRfA4lICPnE26+oVNXT6p0Lo20nY5XC7jyCO",
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
                "base64": r"Ce9HSz/HKKGkIt4uyy+jDuKGA+rLC2cycykMo6vc8jXxqa1UVDYHWq1r+vZKbnnSRBfB981akzRKZCFpC05CTyFqDhXv6OnMjpG97OZEREGIsHEYiJkBW0jJJvfLLgeLsEpBzsro9FztGGXASxyxFRZFhXvHxyiLOKrdWfs7X1O/iK3pEoHMx6uSNSfUOgbebLfIqW7TO++iQS5g1xovXA==",
                "subType": "00"
            }
        },
        "creationDate": {"$date": {"$numberLong": "1552949630483"}},
        "updateDate": {"$date": {"$numberLong": "1552949630483"}},
        "status": {"$numberInt": "0"},
        "masterKey": {"provider": "local"}
    },
    "local:name2": {
        "_id": {
            "$binary": {
                "base64": "local+name2+AAAAAAAAAA==",
                "subType": "04"
            }
        },

        "keyMaterial": {
            "$binary": {
                "base64": r"DX3iUuOlBsx6wBX9UZ3v/qXk1HNeBace2J+h/JwsDdF/vmSXLZ1l1VmZYIcpVFy6ODhdbzLjd4pNgg9wcm4etYig62KNkmtZ0/s1tAL5VsuW/s7/3PYnYGznZTFhLjIVcOH/RNoRj2eQb/sRTyivL85wePEpAU/JzuBj6qO9Y5txQgs1k0J3aNy10R9aQ8kC1NuSSpLAIXwE6DlNDDJXhw==",
                "subType": "00"
            }
        },
        "creationDate": {"$date": {"$numberLong": "1552949630483"}},
        "updateDate": {"$date": {"$numberLong": "1552949630483"}},
        "status": {"$numberInt": "0"},
        "masterKey": {"provider": "local:name2"}
    },
    "azure": {
        "_id": {
            "$binary": {
                "base64": "AZURE+AAAAAAAAAAAAAAAA==",
                "subType": "04"
            }
        },
        "keyMaterial": {
            "$binary": {
                "base64": "n+HWZ0ZSVOYA3cvQgP7inN4JSXfOH85IngmeQxRpQHjCCcqT3IFqEWNlrsVHiz3AELimHhX4HKqOLWMUeSIT6emUDDoQX9BAv8DR1+E1w4nGs/NyEneac78EYFkK3JysrFDOgl2ypCCTKAypkn9CkAx1if4cfgQE93LW4kczcyHdGiH36CIxrCDGv1UzAvERN5Qa47DVwsM6a+hWsF2AAAJVnF0wYLLJU07TuRHdMrrphPWXZsFgyV+lRqJ7DDpReKNO8nMPLV/mHqHBHGPGQiRdb9NoJo8CvokGz4+KE8oLwzKf6V24dtwZmRkrsDV4iOhvROAzz+Euo1ypSkL3mw==",
                "subType": "00"
            }
        },
        "creationDate": {
            "$date": {
                "$numberLong": "1601573901680"
            }
        },
        "updateDate": {
            "$date": {
                "$numberLong": "1601573901680"
            }
        },
        "status": {
            "$numberInt": "0"
        },
        "masterKey": {
            "provider": "azure",
            "keyVaultEndpoint": "key-vault-csfle.vault.azure.net",
            "keyName": "key-name-csfle"
        },
        "keyAltNames": ["altname", "azure_altname"]
    },
    "gcp": {
        "_id": {
            "$binary": {
                "base64": "GCP+AAAAAAAAAAAAAAAAAA==",
                "subType": "04"
            }
        },
        "keyMaterial": {
            "$binary": {
                "base64": "CiQAIgLj0WyktnB4dfYHo5SLZ41K4ASQrjJUaSzl5vvVH0G12G0SiQEAjlV8XPlbnHDEDFbdTO4QIe8ER2/172U1ouLazG0ysDtFFIlSvWX5ZnZUrRMmp/R2aJkzLXEt/zf8Mn4Lfm+itnjgo5R9K4pmPNvvPKNZX5C16lrPT+aA+rd+zXFSmlMg3i5jnxvTdLHhg3G7Q/Uv1ZIJskKt95bzLoe0tUVzRWMYXLIEcohnQg==",
                "subType": "00"
            }
        },
        "creationDate": {
            "$date": {
                "$numberLong": "1601574333107"
            }
        },
        "updateDate": {
            "$date": {
                "$numberLong": "1601574333107"
            }
        },
        "status": {
            "$numberInt": "0"
        },
        "masterKey": {
            "provider": "gcp",
            "projectId": "devprod-drivers",
            "location": "global",
            "keyRing": "key-ring-csfle",
            "keyName": "key-name-csfle"
        },
        "keyAltNames": ["altname", "gcp_altname"]
    },
    "kmip": {
        "_id": {
            "$binary": {
                "base64": "dBHpr8aITfeBQ15grpbLpQ==",
                "subType": "04"
            }
        },
        "keyMaterial": {
            "$binary": {
                "base64": "eUYDyB0HuWb+lQgUwO+6qJQyTTDTY2gp9FbemL7ZFo0pvr0x6rm6Ff9OVUTGH6HyMKipaeHdiIJU1dzsLwvqKvi7Beh+U4iaIWX/K0oEg1GOsJc0+Z/in8gNHbGUYLmycHViM3LES3kdt7FdFSUl5rEBHrM71yoNEXImz17QJWMGOuT4x6yoi2pvnaRJwfrI4DjpmnnTrDMac92jgZehbg==",
                "subType": "00"
            }
        },
        "creationDate": {
            "$date": {
                "$numberLong": "1634220190041"
            }
        },
        "updateDate": {
            "$date": {
                "$numberLong": "1634220190041"
            }
        },
        "status": {
            "$numberInt": "0"
        },
        "masterKey": {
            "provider": "kmip",
            "keyId": "1"
        },
        "keyAltNames": ["altname", "kmip_altname"]
    },
    "kmip_delegated": {
        "_id": {
            "$uuid": "7411e9af-c688-4df7-8143-5e60ae96cba6"
        },
        "keyMaterial": {
            "$binary": {
                "base64": "5TLMFWlguBWe5GUESTvOVtkdBsCrynhnV72XRyZ66/nk+EP9/1oEp1t1sg0+vwCTqULHjBiUE6DRx2mYD/Eup1+u2Jgz9/+1sV1drXeOPALNPkSgiZiDbIb67zRi+wTABEcKcegJH+FhmSGxwUoQAiHCsCbcvia5P8tN1lt98YQ=", "subType": "00"
            }
        },
        "creationDate": {
            "$date": {
                "$numberLong": "1634220190041"
            }
        },
        "updateDate": {
            "$date": {
                "$numberLong": "1634220190041"
            }
        },
        "status": {
            "$numberInt": "0"
        },
        "masterKey": {
            "provider": "kmip",
            "delegated": True,
            "keyId": "11"
        },
        "keyAltNames": ["delegated"]
    }
}

schemas = {
    "basic": {
        "properties": {
            "encrypted_w_altname": {
                "encrypt": {
                    "keyId": "/altname",
                    "bsonType": "string",
                    "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Random"
                }
            },
            "encrypted_string": {
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
            # Same exact as fields as "encrypted_string"
            "encrypted_string_equivalent": {
                "encrypt": {
                    "keyId": [keys["basic"]["_id"]],
                    "bsonType": "string",
                    "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic"
                }
            }
        },
        "bsonType": "object"
    },
    "all": {
        "properties": {
            "encrypted_string_aws": {
                "encrypt": {
                    "keyId": [keys["basic"]["_id"]],
                    "bsonType": "string",
                    "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic"
                }
            },
            "encrypted_string_azure": {
                "encrypt": {
                    "keyId": [keys["azure"]["_id"]],
                    "bsonType": "string",
                    "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic"
                }
            },
            "encrypted_string_gcp": {
                "encrypt": {
                    "keyId": [keys["gcp"]["_id"]],
                    "bsonType": "string",
                    "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic"
                }
            },
            "encrypted_string_local": {
                "encrypt": {
                    "keyId": [keys["local"]["_id"]],
                    "bsonType": "string",
                    "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic"
                }
            },
            "encrypted_string_kmip": {
                "encrypt": {
                    "keyId": [keys["kmip"]["_id"]],
                    "bsonType": "string",
                    "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic"
                }
            },
            "encrypted_string_kmip_delegated": {
                "encrypt": {
                    "keyId": [keys["kmip_delegated"]["_id"]], 
                    "bsonType": "string",
                    "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic"}},
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
            "encrypted_string": {
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
            "encrypted_string": {
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
            "encrypted_string": {
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
                    "encrypted_string": {
                        "encrypt": {
                            "keyId": [keys["basic"]["_id"]],
                            "bsonType": "string",
                            "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Random"
                        }
                    }
                }
            }
        ]
    },
    "noencryption": {
        "properties": {
            "test": {
                "bsonType": "string"
            }
        },
        "bsonType": "object",
        "required": ["test"]
    },
    "local:name2": {
        "properties": {
            "encrypted_string": {
                "encrypt": {
                    "keyId": [keys["local:name2"]["_id"]],
                    "bsonType": "string",
                    "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic"
                }
            }
        },
        "bsonType": "object"
    },
}

ciphertexts = [
    {
        "schema": "basic",
        "field": "encrypted_string",
        "plaintext": "string0",
        "data": {
            "$binary": {
                "base64": "AQAAAAAAAAAAAAAAAAAAAAACwj+3zkv2VM+aTfk60RqhXq6a/77WlLwu/BxXFkL7EppGsju/m8f0x5kBDD3EZTtGALGXlym5jnpZAoSIkswHoA==",
                "subType": "06"
            }
        }
    },
    {
        "schema": "basic",
        "field": "encrypted_string",
        "plaintext": "string1",
        "data": {
            "$binary": {
                "base64": "AQAAAAAAAAAAAAAAAAAAAAACDdw4KFz3ZLquhsbt7RmDjD0N67n0uSXx7IGnQNCLeIKvot6s/ouI21Eo84IOtb6lhwUNPlSEBNY0/hbszWAKJg==",
                "subType": "06"
            }
        }
    },
    {
        "schema": "basic",
        "field": "encrypted_string",
        "plaintext": "string2",
        "data": {
            "$binary": {
                "base64": "AQAAAAAAAAAAAAAAAAAAAAACQ76HWOut3DZtQuV90hp1aaCpZn95vZIaWmn+wrBehcEtcFwyJlBdlyzDzZTWPZCPgiFq72Wvh6Y7VbpU9NAp3A==",
                "subType": "06"
            }
        }
    },
    {
        "schema": "local",
        "field": "encrypted_string",
        "plaintext": "string0",
        "data": {
            "$binary": {
                "base64": "AQAAAAAAAAAAAAAAAAAAAAACV/+zJmpqMU47yxS/xIVAviGi7wHDuFwaULAixEAoIh0xHz73UYOM3D8D44gcJn67EROjbz4ITpYzzlCJovDL0Q==",
                "subType": "06"
            }
        }
    },
    {
        "schema": "basic",
        "field": "encrypted_objectId",
        "plaintext": "test",
        "data": {
            "$binary": {
                "base64": "AQAAAAAAAAAAAAAAAAAAAAAHmkTPqvzfHMWpvS1mEsrjOxVQ2dyihEgIFWD5E0eNEsiMBQsC0GuvjdqYRL5DHLFI1vKuGek7EYYp0Qyii/tHqA==",
                "subType": "06"
            }
        }
    },
    {
        "schema": "basic",
        "field": "encrypted_symbol",
        "plaintext": "test",
        "data": {
            "$binary": {
                "base64": "AQAAAAAAAAAAAAAAAAAAAAAOOmvDmWjcuKsSCO7U/7t9HJ8eI73B6wduyMbdkvn7n7V4uTJes/j+BTtneSdyG2JHKHGkevWAJSIU2XoO66BSXw==",
                "subType": "06"
            }
        }
    },
    {
        "schema": "basic",
        "field": "encrypted_int32",
        "plaintext": "test",
        "data": {
            "$binary": {
                "base64": "AQAAAAAAAAAAAAAAAAAAAAAQPNXJVXMEjGZnftMuf2INKufXCtQIRHdw5wTgn6QYt3ejcoAXyiwI4XIUizkpsob494qpt2in4tWeiO7b9zkA8Q==",
                "subType": "06"
            }
        }
    },
    {
        "schema": "basic",
        "field": "encrypted_int64",
        "plaintext": "test",
        "data": {
            "$binary": {
                "base64": "AQAAAAAAAAAAAAAAAAAAAAACKWM29kOcLsfSLfJJ3SSmLr+wgrTtpu1lads1NzDz80AjMyrstw/GMdCuzX+AS+JS84Si2cT1WPMemTkBdVdGAw==",
                "subType": "06"
            }
        }
    },
    {
        "schema": "basic",
        "field": "encrypted_binData",
        "plaintext": "test",
        "data": {
            "$binary": {
                "base64": "AQAAAAAAAAAAAAAAAAAAAAAFB/KHZQHaHHo8fctcl7v6kR+sLkJoTRx2cPSSck9ya+nbGROSeFhdhDRHaCzhV78fDEqnMDSVPNi+ZkbaIh46GQ==",
                "subType": "06"
            }
        }
    },
    {
        "schema": "basic",
        "field": "encrypted_javascript",
        "plaintext": "test",
        "data": {
            "$binary": {
                "base64": "AQAAAAAAAAAAAAAAAAAAAAANrvMgJkTKWGMc9wt3E2RBR2Hu5gL9p+vIIdHe9FcOm99t1W480/oX1Gnd87ON3B399DuFaxi/aaIiQSo7gTX6Lw==",
                "subType": "06"
            }
        }
    },
    {
        "schema": "basic",
        "field": "encrypted_timestamp",
        "plaintext": "test",
        "data": {
            "$binary": {
                "base64": "AQAAAAAAAAAAAAAAAAAAAAARJHaM4Gq3MpDTdBasBsEolQaOmxJQU1wsZVaSFAOLpEh1QihDglXI95xemePFMKhg+KNpFg7lw1ChCs2Wn/c26Q==",
                "subType": "06"
            }
        }
    },
    {
        "schema": "basic",
        "field": "encrypted_regex",
        "plaintext": "test",
        "data": {
            "$binary": {
                "base64": "AQAAAAAAAAAAAAAAAAAAAAALVnxM4UqGhqf5eXw6nsS08am3YJrTf1EvjKitT8tyyMAbHsICIU3GUjuC7EBofCHbusvgo7pDyaClGostFz44nA==",
                "subType": "06"
            }
        }
    },
    {
        "schema": "basic",
        "field": "encrypted_dbPointer",
        "plaintext": "test",
        "data": {
            "$binary": {
                "base64": "AQAAAAAAAAAAAAAAAAAAAAACKWM29kOcLsfSLfJJ3SSmLr+wgrTtpu1lads1NzDz80AjMyrstw/GMdCuzX+AS+JS84Si2cT1WPMemTkBdVdGAw==",
                "subType": "06"
            }
        }
    },
    {
        "schema": "basic",
        "field": "encrypted_date",
        "plaintext": "test",
        "data": {
            "$binary": {
                "base64": "AQAAAAAAAAAAAAAAAAAAAAAJ5sN7u6l97+DswfKTqZAijSTSOo5htinGKQKUD7pHNJYlLXGOkB4glrCu7ibu0g3344RHQ5yUp4YxMEa8GD+Snw==",
                "subType": "06"
            }
        }
    },
    {
        "schema": "basic",
        "field": "random",
        "plaintext": "abc",
        "data": {
            "$binary": {
                "base64": "AgAAAAAAAAAAAAAAAAAAAAACyfp+lXvKOi7f5vh6ZsCijLEaXFKq1X06RmyS98ZvmMQGixTw8HM1f/bGxZjGwvYwjXOkIEb7Exgb8p2KCDI5TQ==",
                "subType": "06"
            }
        }
    },
    {
        "schema": "all",
        "field": "encrypted_string_azure",
        "plaintext": "string0",
        "data": {
            "$binary": {
                "base64": "AQGVERPgAAAAAAAAAAAAAAAC5DbBSwPwfSlBrDtRuglvNvCXD1KzDuCKY2P+4bRFtHDjpTOE2XuytPAUaAbXf1orsPq59PVZmsbTZbt2CB8qaQ==",
                "subType": "06"
            }
        }
    },
    {
        "schema": "all",
        "field": "encrypted_string_gcp",
        "plaintext": "string0",
        "data": {
            "$binary": {
                "base64": "ARgj/gAAAAAAAAAAAAAAAAACwFd+Y5Ojw45GUXNvbcIpN9YkRdoHDHkR4kssdn0tIMKlDQOLFkWFY9X07IRlXsxPD8DcTiKnl6XINK28vhcGlg==",
                "subType": "06"
            }
        }
    },
    {
        "schema": "all",
        "field": "encrypted_string_kmip",
        "plaintext": "string0",
        "data": {
            "$binary": {
                "base64": "AXQR6a/GiE33gUNeYK6Wy6UCKCwtKFIsL8eKObDVxvqGupJNUk7kXswHhB7G5j/C1D+6no+Asra0KgSU43bTL3ooIBLVyIzbV5CDJYqzAsa4WQ==",
                "subType": "06"
            }
        }
    },
    {
        "schema": "all",
        "field": "encrypted_string_kmip_delegated",
        "plaintext": "string0",
        "data": {
            "$binary": {
                "base64": "AXQR6a/GiE33gUNeYK6Wy6YCkB+8NVfAAjIbvLqyXIg6g1a8tXrym92DPoqmxpcdQyH0vQM3aFNMz7tZwQBimKs29ztZV/LWjM633HhO5ACl9A==",
                "subType": "06"
            }
        }
    },
    {
        "schema": "local:name2",
        "field": "encrypted_string",
        "plaintext": "string0",
        "data": {
            "$binary": {
                "base64": "AZaHGpfp2pntvgAAAAAAAAAC07sFvTQ0I4O2U49hpr4HezaK44Ivluzv5ntQBTYHDlAJMLyRMyB6Dl+UGHBgqhHe/Xw+pcT9XdiUoOJYAx9g+w==",
                "subType": "06"
            }
        }
    },
]


def schema(name="basic"):
    return schemas[name]


def schema_w_type(type):
    schema = {
        "properties": {},
        "bsonType": "object"
    }
    schema["properties"]["encrypted_" + type] = {"encrypt": {
        "keyId": [keys["basic"]["_id"]],
        "bsonType": type,
        "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic"
    }
    }
    return schema


def key(name="basic"):
    return keys[name]


def ciphertext(plaintext, field, schema="basic"):
    for ciphertext in ciphertexts:
        if schema == ciphertext["schema"] and field == ciphertext["field"] and plaintext == ciphertext["plaintext"]:
            return ciphertext["data"]
    raise Exception("Ciphertext needs to be pre-generated")


def local_provider(name=None):
    if name is not None:
        if name == "name2":
            return {
                "key": {"$binary": {"base64": "local+name2+YUJCa1kxNkVyNUR1QURhZ2h2UzR2d2RrZzh0cFBwM3R6NmdWMDFBMUN3YkQ5aXRRMkhGRGdQV09wOGVNYUMxT2k3NjZKelhaQmRCZGJkTXVyZG9uSjFk", "subType": "00"}}
            }        
        else:
            raise Exception ("Unexpected name '{}'".format(name))
    
    return {
        "key": {"$binary": {"base64": "Mng0NCt4ZHVUYUJCa1kxNkVyNUR1QURhZ2h2UzR2d2RrZzh0cFBwM3R6NmdWMDFBMUN3YkQ5aXRRMkhGRGdQV09wOGVNYUMxT2k3NjZKelhaQmRCZGJkTXVyZG9uSjFk", "subType": "00"}}
    }

def yamlfile (relative_filepath):
    filepath = Path("./source/client-side-encryption/etc/data") / Path(relative_filepath)
    with open(filepath, "r") as file:
        contents = file.read()
        return yaml.safe_load (contents)

if sys.version_info < (3, 0):
    print("Use Python 3")
    sys.exit(1)

if len(sys.argv) < 3:
    print(description)
    print("usage: python generate-test.py ./test-templates/<filename>.yml.template [...] <target directory>")
    print("example: python ./generate-test.py ./test-templates/bulk.yml.template ./")
    sys.exit(1)

targetdir = sys.argv[-1]

for filepath in sys.argv[1:-1]:
    filedir = os.path.dirname(filepath)
    (filename, ext) = os.path.splitext(os.path.basename(filepath))
    if ext != ".template":
        print("Input file must end with .yml.template")
        sys.exit(1)
    (filename, ext) = os.path.splitext(filename)
    if ext != ".yml":
        print("Input file must end with .yml.template")
        sys.exit(1)

    template = Template(open(filepath, "r").read())
    injections = {
        "schema": schema,
        "ciphertext": ciphertext,
        "key": key,
        "local_provider": local_provider,
        "schema_w_type": schema_w_type,
        "yamlfile": yamlfile,
    }

    rendered = template.render(**injections)
    # check for valid YAML.
    parsed = yaml.load(rendered, Loader=yaml.Loader)
    open(f"{os.path.join(targetdir,filename + '.yml')}", "w").write(rendered)
    print(f"Generated {os.path.join(targetdir,filename)}.yml")
    print("""Run "make" from specifications/source directory to generate corresponding JSON file""")
