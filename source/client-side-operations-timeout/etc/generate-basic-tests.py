from collections import namedtuple
from jinja2 import Template
import os
import sys

# TODO: do tests distinguish between createIndex and createIndexes?

Operation = namedtuple('Operation', ['operation_name', 'command_name', 'object', 'arguments'])

CLIENT_OPERATIONS = [
    Operation('listDatabases', 'listDatabases', 'client', ['filter: {}']),
    Operation('listDatabaseNames', 'listDatabases', 'client', ['filter: {}']),
    Operation('createChangeStream', 'aggregate', 'client', ['pipeline: []'])
]

DB_OPERATIONS = [
    Operation('aggregate', 'aggregate', 'database', ['pipeline: [ { $listLocalSessions: {} }, { $limit: 1 } ]']),
    Operation('listCollections', 'listCollections', 'database', ['filter: {}']),
    Operation('listCollectionNames', 'listCollections', 'database', ['filter: {}']),
    Operation('runCommand', 'ping', 'database', ['command: { ping: 1 }']),
    Operation('createChangeStream', 'aggregate', 'database', ['pipeline: []'])
]

INSERT_MANY_ARGUMENTS = '''documents:
            - { x: 1 }'''

BULK_WRITE_ARGUMENTS = '''requests:
            - insertOne:
                document: { _id: 1 }'''

COLLECTION_OPERATIONS = [
    Operation('aggregate', 'aggregate', 'collection', ['pipeline: []']),
    Operation('count', 'count', 'collection', ['filter: {}']),
    Operation('countDocuments', 'aggregate', 'collection', ['filter: {}']),
    Operation('estimatedDocumentCount', 'count', 'collection', []),
    Operation('distinct', 'distinct', 'collection', ['fieldName: x', 'filter: {}']),
    Operation('find', 'find', 'collection', ['filter: {}']),
    Operation('findOne', 'find', 'collection', ['filter: {}']),
    Operation('listIndexes', 'listIndexes', 'collection', []),
    Operation('listIndexNames', 'listIndexes', 'collection', []),
    Operation('createChangeStream', 'aggregate', 'collection', ['pipeline: []']),
    Operation('insertOne', 'insert', 'collection', ['document: { x: 1 }']),
    Operation('insertMany', 'insert', 'collection', [INSERT_MANY_ARGUMENTS]),
    Operation('deleteOne', 'delete', 'collection', ['filter: {}']),
    Operation('deleteMany', 'delete', 'collection', ['filter: {}']),
    Operation('replaceOne', 'update', 'collection', ['filter: {}', 'replacement: { x: 1 }']),
    Operation('updateOne', 'update', 'collection', ['filter: {}', 'update: { $set: { x: 1 } }']),
    Operation('updateMany', 'update', 'collection', ['filter: {}', 'update: { $set: { x: 1 } }']),
    Operation('findOneAndDelete', 'findAndModify', 'collection', ['filter: {}']),
    Operation('findOneAndReplace', 'findAndModify', 'collection', ['filter: {}', 'replacement: { x: 1 }']),
    Operation('findOneAndUpdate', 'findAndModify', 'collection', ['filter: {}', 'update: { $set: { x: 1 } }']),
    Operation('bulkWrite', 'insert', 'collection', [BULK_WRITE_ARGUMENTS]),
    Operation('createIndex', 'createIndexes', 'collection', ['keys: { x: 1 }', 'name: "x_1"']),
    Operation('dropIndex', 'dropIndexes', 'collection', ['name: "x_1"']),
    Operation('dropIndexes', 'dropIndexes', 'collection', []),
]

# Should only be used for client-side validation tests.
SESSION_OPERATIONS = [
    Operation('commitTransaction', 'commitTransaction', 'session', []),
    Operation('abortTransaction', 'abortTransaction', 'session', []),
    Operation('withTransaction', 'insert', 'session', ['callback: []']),
]

# Should only be used for client-side validation tests.
GRIDFS_OPERATIONS = [
    Operation('upload', '', 'bucket', ['filename: filename', 'source: { $$hexBytes: "1122334455" }']),
    Operation('download', '', 'bucket', ['id: nonExistentId']),
    Operation('delete', '', 'bucket', ['id: nonExistentId']),
    Operation('find', '', 'bucket', ['filter: {}']),
    Operation('rename', '', 'bucket', ['id: nonExistentId', 'newFilename: newName']),
    Operation('drop', '', 'bucket', []),
]

# Session and GridFS operations are generally tested in other files, so they're not included in the list of all
# operations. Individual generation functions can choose to include them if needed.
OPERATIONS = CLIENT_OPERATIONS + DB_OPERATIONS + COLLECTION_OPERATIONS

RETRYABLE_WRITE_OPERATIONS = [op for op in OPERATIONS if op.operation_name in 
    ['insertOne', 'updateOne', 'deleteOne', 'replaceOne', 'findOneAndDelete', 'findOneAndUpdate', 'findOneAndReplace', 'insertMany']
]

RETRYABLE_READ_OPERATIONS = [op for op in OPERATIONS if op.operation_name in
    ['find', 'findOne', 'aggregate', 'distinct', 'count', 'estimatedDocumentCount', 'countDocuments', 'createChangeStream', 'listDatabases',
    'listDatabaseNames', 'listCollections', 'listCollectionNames', 'listIndexes']
]

templates_dir = sys.argv[1]
tests_dir = sys.argv[2]

def get_template(file):
    path = f'{templates_dir}/{file}.yml.template'
    return Template(open(path, 'r').read())

def write_yaml(file, template, injections):
    rendered = template.render(**injections)
    path = f'{tests_dir}/{file}.yml'
    open(path, 'w').write(rendered)

def get_command_object(object):
    if object == 'client' or object == 'database':
        return 1
    return '*collectionName'

def max_time_supported(operation_name):
    return operation_name in ['aggregate', 'count', 'estimatedDocumentCount', 'distinct', 'find', 'findOne',
    'findOneAndDelete', 'findOneAndReplace', 'findOneAndUpdate', 'createIndex', 'dropIndex', 'dropIndexes']

def generate(name, operations):
    template = get_template(name)
    injections = {
        'operations': operations,
        'get_command_object': get_command_object,
        'max_time_supported': max_time_supported,
    }
    write_yaml(name, template, injections)

def generate_global_timeout_tests():
    generate('global-timeoutMS', OPERATIONS)

def generate_override_db():
    generate('override-database-timeoutMS', DB_OPERATIONS + COLLECTION_OPERATIONS)

def generate_override_coll():
    generate('override-collection-timeoutMS', COLLECTION_OPERATIONS)

def generate_override_operation():
    generate('override-operation-timeoutMS', OPERATIONS)

def generate_retryable():
    generate('retryability-timeoutMS', RETRYABLE_WRITE_OPERATIONS + RETRYABLE_READ_OPERATIONS)
    generate('retryability-legacy-timeouts', RETRYABLE_WRITE_OPERATIONS + RETRYABLE_READ_OPERATIONS)

def generate_deprecated():
    generate('deprecated-options', OPERATIONS + SESSION_OPERATIONS + GRIDFS_OPERATIONS)

generate_global_timeout_tests()
generate_override_db()
generate_override_coll()
generate_override_operation()
generate_retryable()
generate_deprecated()
