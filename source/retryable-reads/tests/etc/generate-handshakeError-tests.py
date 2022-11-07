from collections import namedtuple
from jinja2 import Template
import os
import sys

Operation = namedtuple(
    'Operation', ['operation_name', 'command_name', 'object', 'arguments'])

CLIENT_OPERATIONS = [
    Operation('listDatabases', 'listDatabases', 'client', ['filter: {}']),
    Operation('listDatabaseNames', 'listDatabases', 'client', []),
    Operation('createChangeStream', 'aggregate', 'client', ['pipeline: []'])
]

RUN_COMMAND_ARGUMENTS = '''command: { ping: 1 }
          commandName: ping'''

DB_OPERATIONS = [
    Operation('aggregate', 'aggregate', 'database', [
              'pipeline: [ { $listLocalSessions: {} }, { $limit: 1 } ]']),
    Operation('listCollections', 'listCollections',
              'database', ['filter: {}']),
    Operation('listCollectionNames', 'listCollections',
              'database', ['filter: {}']),
    Operation('runCommand', 'ping', 'database', [RUN_COMMAND_ARGUMENTS]),
    Operation('createChangeStream', 'aggregate', 'database', ['pipeline: []'])
]

INSERT_MANY_ARGUMENTS = '''documents:
            - { x: 1 }'''

BULK_WRITE_ARGUMENTS = '''requests:
            - insertOne:
                document: { _id: 1 }'''

COLLECTION_READ_OPERATIONS = [
    Operation('aggregate', 'aggregate', 'collection', ['pipeline: []']),
    # Operation('count', 'count', 'collection', ['filter: {}']), # Deprecated.
    Operation('countDocuments', 'aggregate', 'collection', ['filter: {}']),
    Operation('estimatedDocumentCount', 'count', 'collection', []),
    Operation('distinct', 'distinct', 'collection',
              ['fieldName: x', 'filter: {}']),
    Operation('find', 'find', 'collection', ['filter: {}']),
    # Operation('findOne', 'find', 'collection', ['filter: {}']), # Optional.
    Operation('listIndexes', 'listIndexes', 'collection', []),
    Operation('listIndexNames', 'listIndexes', 'collection', []),
    Operation('createChangeStream', 'aggregate',
              'collection', ['pipeline: []']),
]
COLLECTION_WRITE_OPERATIONS = [
    Operation('insertOne', 'insert', 'collection', ['document: { x: 1 }']),
    Operation('insertMany', 'insert', 'collection', [INSERT_MANY_ARGUMENTS]),
    Operation('deleteOne', 'delete', 'collection', ['filter: {}']),
    Operation('deleteMany', 'delete', 'collection', ['filter: {}']),
    Operation('replaceOne', 'update', 'collection', [
              'filter: {}', 'replacement: { x: 1 }']),
    Operation('updateOne', 'update', 'collection', [
              'filter: {}', 'update: { $set: { x: 1 } }']),
    Operation('updateMany', 'update', 'collection', [
              'filter: {}', 'update: { $set: { x: 1 } }']),
    Operation('findOneAndDelete', 'findAndModify',
              'collection', ['filter: {}']),
    Operation('findOneAndReplace', 'findAndModify', 'collection',
              ['filter: {}', 'replacement: { x: 1 }']),
    Operation('findOneAndUpdate', 'findAndModify', 'collection',
              ['filter: {}', 'update: { $set: { x: 1 } }']),
    Operation('bulkWrite', 'insert', 'collection', [BULK_WRITE_ARGUMENTS]),
    Operation('createIndex', 'createIndexes', 'collection',
              ['keys: { x: 1 }', 'name: "x_1"']),
    Operation('dropIndex', 'dropIndexes', 'collection', ['name: "x_1"']),
    Operation('dropIndexes', 'dropIndexes', 'collection', []),
]
COLLECTION_OPERATIONS = COLLECTION_READ_OPERATIONS + COLLECTION_WRITE_OPERATIONS

# Session and GridFS operations are generally tested in other files, so they're not included in the list of all
# operations. Individual generation functions can choose to include them if needed.
OPERATIONS = CLIENT_OPERATIONS + DB_OPERATIONS + COLLECTION_OPERATIONS

RETRYABLE_READ_OPERATIONS = [op for op in OPERATIONS if op.operation_name in
                             ['find', 'findOne', 'aggregate', 'distinct', 'count', 'estimatedDocumentCount', 'countDocuments', 'createChangeStream', 'listDatabases',
                              'listDatabaseNames', 'listCollections', 'listCollectionNames', 'listIndexes']
                             ]


# ./source/retryable-reads/tests/etc
DIR = os.path.dirname(os.path.realpath(__file__))

# ./source/retryable-reads/tests/etc/templates
TEMPLATES_DIR = f'{DIR}/templates'

# ./source/retryable-reads/tests/unified
TESTS_DIR = f'{os.path.dirname(DIR)}/unified'


def get_template(file):
    path = f'{TEMPLATES_DIR}/{file}.yml.template'
    return Template(open(path, 'r').read())


def write_yaml(file, template, injections):
    rendered = template.render(**injections)
    path = f'{TESTS_DIR}/{file}.yml'
    open(path, 'w').write(rendered)


def generate(name, operations):
    template = get_template(name)
    injections = {
        'operations': operations,
    }
    write_yaml(name, template, injections)


def generate_handshake_error_tests():
    generate('handshakeError', RETRYABLE_READ_OPERATIONS)


generate_handshake_error_tests()
