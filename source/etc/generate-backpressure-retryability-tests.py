from collections import namedtuple
from jinja2 import Template
import os

Operation = namedtuple(
    'Operation', ['operation_name', 'command_name', 'object', 'arguments', 'operation_type'])

CLIENT_BULK_WRITE_ARGUMENTS = '''models:
          - insertOne:
              namespace: *client_bulk_write_ns
              document: { _id: 8, x: 88 }'''

CLIENT_OPERATIONS = [
    Operation('listDatabases', 'listDatabases', 'client', ['filter: {}'], 'read'),
    Operation('listDatabaseNames', 'listDatabases', 'client', [], 'read'),
    Operation('createChangeStream', 'aggregate', 'client', ['pipeline: []'], 'read'),
    Operation('clientBulkWrite', 'bulkWrite', 'client', [CLIENT_BULK_WRITE_ARGUMENTS], 'write')
]

RUN_COMMAND_ARGUMENTS = '''command: { ping: 1 }
          commandName: ping'''

DB_OPERATIONS = [
    Operation('aggregate', 'aggregate', 'database', [
              'pipeline: [ { $listLocalSessions: {} }, { $limit: 1 } ]'], 'read'),
    Operation('listCollections', 'listCollections',
              'database', ['filter: {}'], 'read'),
    Operation('listCollectionNames', 'listCollections',
              'database', ['filter: {}'], 'read'), # Optional.
    Operation('runCommand', 'ping', 'database', [RUN_COMMAND_ARGUMENTS], 'read'),
    Operation('createChangeStream', 'aggregate', 'database', ['pipeline: []'], 'read')
]

INSERT_MANY_ARGUMENTS = '''documents:
            - { _id: 2, x: 22 }'''

BULK_WRITE_ARGUMENTS = '''requests:
            - insertOne:
                document: { _id: 2, x: 22 }'''

COLLECTION_READ_OPERATIONS = [
    Operation('aggregate', 'aggregate', 'collection', ['pipeline: []'], 'read'),
    # Operation('count', 'count', 'collection', ['filter: {}'], 'read'),  # Deprecated.
    Operation('countDocuments', 'aggregate', 'collection', ['filter: {}'], 'read'),
    Operation('estimatedDocumentCount', 'count', 'collection', [], 'read'),
    Operation('distinct', 'distinct', 'collection',
              ['fieldName: x', 'filter: {}'], 'read'),
    Operation('find', 'find', 'collection', ['filter: {}'], 'read'),
    Operation('findOne', 'find', 'collection', ['filter: {}'], 'read'),  # Optional.
    Operation('listIndexes', 'listIndexes', 'collection', [], 'read'),
    Operation('listIndexNames', 'listIndexes', 'collection', [], 'read'),  # Optional.
    Operation('createChangeStream', 'aggregate',
              'collection', ['pipeline: []'], 'read'),
]

COLLECTION_WRITE_OPERATIONS = [
    Operation('insertOne', 'insert', 'collection',
              ['document: { _id: 2, x: 22 }'], 'write'),
    Operation('insertMany', 'insert', 'collection', [INSERT_MANY_ARGUMENTS], 'write'),
    Operation('deleteOne', 'delete', 'collection', ['filter: {}'], 'write'),
    Operation('deleteMany', 'delete', 'collection', ['filter: {}'], 'write'),
    Operation('replaceOne', 'update', 'collection', [
              'filter: {}', 'replacement: { x: 22 }'], 'write'),
    Operation('updateOne', 'update', 'collection', [
              'filter: {}', 'update: { $set: { x: 22 } }'], 'write'),
    Operation('updateMany', 'update', 'collection', [
              'filter: {}', 'update: { $set: { x: 22 } }'], 'write'),
    Operation('findOneAndDelete', 'findAndModify',
              'collection', ['filter: {}'], 'write'),
    Operation('findOneAndReplace', 'findAndModify', 'collection',
              ['filter: {}', 'replacement: { x: 22 }'], 'write'),
    Operation('findOneAndUpdate', 'findAndModify', 'collection',
              ['filter: {}', 'update: { $set: { x: 22 } }'], 'write'),
    Operation('bulkWrite', 'insert', 'collection', [BULK_WRITE_ARGUMENTS], 'write'),
    Operation('createIndex', 'createIndexes', 'collection',
              ['keys: { x: 11 }', 'name: "x_11"'], 'write'),
    Operation('dropIndex', 'dropIndexes', 'collection', ['name: "x_11"'], 'write'),
    Operation('dropIndexes', 'dropIndexes', 'collection', [], 'write'),
    Operation('aggregate', 'aggregate', 'collection', ['pipeline: [{$out: "output"}]'], 'write'),
]

COLLECTION_OPERATIONS = COLLECTION_READ_OPERATIONS + COLLECTION_WRITE_OPERATIONS

# Session and GridFS operations are generally tested in other files, so they're not included in the list of all
# operations. Individual generation functions can choose to include them if needed.
OPERATIONS = CLIENT_OPERATIONS + DB_OPERATIONS + COLLECTION_OPERATIONS

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


def generate_retry_loop_tests():
    templates_dir = f'{os.path.dirname(DIR)}/client-backpressure/tests'
    tests_dir = f'{os.path.dirname(DIR)}/client-backpressure/tests'
    generate('backpressure-retry-loop', templates_dir,
             tests_dir, OPERATIONS)


def generate_max_attempts_tests():
    templates_dir = f'{os.path.dirname(DIR)}/client-backpressure/tests'
    tests_dir = f'{os.path.dirname(DIR)}/client-backpressure/tests'
    generate('backpressure-retry-max-attempts', templates_dir,
             tests_dir, OPERATIONS)

generate_retry_loop_tests()
generate_max_attempts_tests()
