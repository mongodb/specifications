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
            - { _id: 2, x: 22 }'''

BULK_WRITE_ARGUMENTS = '''requests:
            - insertOne:
                document: { _id: 2, x: 22 }'''

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
    Operation('insertOne', 'insert', 'collection',
              ['document: { _id: 2, x: 22 }']),
    Operation('insertMany', 'insert', 'collection', [INSERT_MANY_ARGUMENTS]),
    Operation('deleteOne', 'delete', 'collection', ['filter: {}']),
    Operation('deleteMany', 'delete', 'collection', ['filter: {}']),
    Operation('replaceOne', 'update', 'collection', [
              'filter: {}', 'replacement: { x: 22 }']),
    Operation('updateOne', 'update', 'collection', [
              'filter: {}', 'update: { $set: { x: 22 } }']),
    Operation('updateMany', 'update', 'collection', [
              'filter: {}', 'update: { $set: { x: 22 } }']),
    Operation('findOneAndDelete', 'findAndModify',
              'collection', ['filter: {}']),
    Operation('findOneAndReplace', 'findAndModify', 'collection',
              ['filter: {}', 'replacement: { x: 22 }']),
    Operation('findOneAndUpdate', 'findAndModify', 'collection',
              ['filter: {}', 'update: { $set: { x: 22 } }']),
    Operation('bulkWrite', 'insert', 'collection', [BULK_WRITE_ARGUMENTS]),
    Operation('createIndex', 'createIndexes', 'collection',
              ['keys: { x: 11 }', 'name: "x_11"']),
    Operation('dropIndex', 'dropIndexes', 'collection', ['name: "x_11"']),
    Operation('dropIndexes', 'dropIndexes', 'collection', []),
]

COLLECTION_OPERATIONS = COLLECTION_READ_OPERATIONS + COLLECTION_WRITE_OPERATIONS

# Session and GridFS operations are generally tested in other files, so they're not included in the list of all
# operations. Individual generation functions can choose to include them if needed.
OPERATIONS = CLIENT_OPERATIONS + DB_OPERATIONS + COLLECTION_OPERATIONS

RETRYABLE_READ_OPERATIONS = [op for op in OPERATIONS if op.operation_name in
                             ['find',
                              'findOne',
                              'aggregate',
                              'distinct',
                              'count',
                              'estimatedDocumentCount',
                              'countDocuments',
                              'createChangeStream',
                              'listDatabases',
                              'listDatabaseNames',
                              'listCollections',
                              'listCollectionNames',
                              'listIndexes',
                              ]
                             ]

RETRYABLE_WRITE_OPERATIONS = [op for op in OPERATIONS if op.operation_name in
                              ['insertOne',
                               'updateOne',
                               'deleteOne',
                               'replaceOne',
                               'findOneAndDelete',
                               'findOneAndUpdate',
                               'findOneAndReplace',
                               'insertMany',
                               'bulkWrite',
                               ]
                              ]


# ./source/etc
DIR = os.path.dirname(os.path.realpath(__file__))


def get_template(file, templates_dir):
    path = f'{templates_dir}/{file}.yml.template'
    return Template(open(path, 'r').read())


def write_yaml(file, template, tests_dir, injections):
    rendered = template.render(**injections)
    path = f'{tests_dir}/{file}.yml'
    open(path, 'w').write(rendered)


def generate(name, templates_dir, tests_dir, operations):
    template = get_template(name, templates_dir)
    injections = {
        'operations': operations,
    }
    write_yaml(name, template, tests_dir, injections)


def generate_retryable_reads_handshake_error_tests():
    # ./source/retryable-reads/tests/etc/templates
    templates_dir = f'{os.path.dirname(DIR)}/retryable-reads/tests/etc/templates'
    # ./source/retryable-reads/tests/unified
    tests_dir = f'{os.path.dirname(DIR)}/retryable-reads/tests/unified'
    generate('handshakeError', templates_dir,
             tests_dir, RETRYABLE_READ_OPERATIONS)


def generate_retryable_writes_handshake_error_tests():
    # ./source/retryable-writes/tests/etc/templates
    templates_dir = f'{os.path.dirname(DIR)}/retryable-writes/tests/etc/templates'
    # ./source/retryable-writes/tests/unified
    tests_dir = f'{os.path.dirname(DIR)}/retryable-writes/tests/unified'
    generate('handshakeError', templates_dir,
             tests_dir, RETRYABLE_WRITE_OPERATIONS)


generate_retryable_reads_handshake_error_tests()
generate_retryable_writes_handshake_error_tests()
