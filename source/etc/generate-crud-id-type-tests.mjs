import fs from 'node:fs/promises';
import path from 'node:path';

import yaml from 'js-yaml';

const operations = {
  insertOne: _id => {
    return {
      name: 'insertOne',
      object: 'collection',
      arguments: { document: { _id } }
    };
  },
  insertMany: _id => {
    return {
      name: 'insertMany',
      object: 'collection',
      arguments: { documents: [{ _id }] }
    };
  },
  updateOne: _id => {
    return {
      name: 'updateOne',
      object: 'collection',
      arguments: { filter: { _id }, update: { $unset: { a: '' } }, upsert: true }
    };
  },
  updateMany: _id => {
    return {
      name: 'updateMany',
      object: 'collection',
      arguments: { filter: { _id }, update: { $unset: { a: '' } }, upsert: true }
    };
  },
  replaceOne: _id => {
    return {
      name: 'replaceOne',
      object: 'collection',
      arguments: { filter: {}, replacement: { _id }, upsert: true }
    };
  },
  bulkWrite: _id => {
    return {
      name: 'bulkWrite',
      object: 'collection',
      arguments: { requests: [{ insertOne: { document: { _id } } }] }
    };
  },
  clientBulkWrite: _id => {
    return {
      name: 'clientBulkWrite',
      object: 'client',
      arguments: { models: [{ insertOne: { namespace: 'crud_id.type_tests', document: { _id } } }] }
    };
  }
};

const idTypes = {
  double: { $numberDouble: 'NaN' },
  string: '',
  object: {},
  binData: { $binary: { base64: '', subType: '00' } },
  undefined: { $undefined: true },
  objectId: { $oid: '507f1f77bcf86cd799439011' },
  bool: false,
  date: { $date: { $numberLong: '0' } },
  null: null,
  dbPointer: { $dbPointer: { $ref: 'a.b', $id: { $oid: '507f1f77bcf86cd799439011' } } },
  javascript: { $code: '' },
  javascriptWithScope: { $code: '', $scope: {} },
  symbol: { $symbol: '' },
  int: { $numberInt: '0' },
  timestamp: { $timestamp: { t: 0, i: 0 } },
  long: { $numberLong: '0' },
  decimal: { $numberDecimal: '0' },
  minKey: { $minKey: 1 },
  maxKey: { $maxKey: 1 }
};

// This is defined by the server
const illegalIdTypes = {
  regex: { $regularExpression: { pattern: 'abc', options: 'i' } },
  array: []
};

const unifiedTestSuite = () => ({
  description: 'CRUD ID Type Tests',
  schemaVersion: '1.0',
  createEntities: [
    { client: { id: 'client', observeEvents: ['commandStartedEvent'] } },
    { database: { id: 'database', client: 'client', databaseName: 'crud_id' } },
    { collection: { id: 'collection', database: 'database', collectionName: 'type_tests' } }
  ],
  tests: [
    ...Object.entries(idTypes).flatMap(([idName, idValue]) =>
      Object.entries(operations).flatMap(([operationName, operation]) => ({
        description: `inserting _id with type ${idName} via ${operationName}`,

        // If the operation is clientBulkWrite, we need to run on server version 8.0 or higher
        ...(operationName === 'clientBulkWrite'
          ? { runOnRequirements: [{ minServerVersion: '8.0' }] }
          : {}),

        // We need to make sure the collection is empty before inserting anything to avoid duplicate _id errors
        operations: [
          { name: 'dropCollection', object: 'database', arguments: { collection: 'type_tests' } },
          operation(idValue)
        ],

        // The collection should always have one document with the _id we inserted
        outcome: [
          { databaseName: 'crud_id', collectionName: 'type_tests', documents: [{ _id: idValue }] }
        ]

        // It might be nicer to communicate the assertion drivers should be making: { _id: { $$type: idName } }
        // Rather than type equality to avoid EJSON parse settings getting in the way
        // but we need to change unified runners to use their matching code on outcome instead of simple deep equality check
      }))
    ),

    ...Object.entries(illegalIdTypes)
      .flatMap(([idName, idValue]) =>
        Object.entries(operations).flatMap(([operationName, operation]) => ({
          description: `drivers should not prevent _id with type ${idName} to insert via ${operationName}`,

          // If the operation is clientBulkWrite, we need to run on server version 8.0 or higher
          ...(operationName === 'clientBulkWrite'
            ? { runOnRequirements: [{ minServerVersion: '8.0' }] }
            : {}),

          // We need to make sure the collection is empty before inserting anything to avoid duplicate _id errors
          operations: [
            { name: 'dropCollection', object: 'database', arguments: { collection: 'type_tests' } },
            { ...operation(idValue), expectError: { isClientError: false } }
          ]
        }))
      )
      .filter(
        test =>
          !(
            // updates that have a regex in the filter will not upsert the regex as the _id
            (
              (test.operations[1].name === 'updateOne' ||
                test.operations[1].name === 'updateMany') &&
              test.description.includes('_id with type regex')
            )
          )
      )
  ]
});

const sourceDirectory = path.resolve(import.meta.dirname, '..');
await fs.writeFile(
  path.join(sourceDirectory, 'crud', 'tests', 'unified', 'create-id-types.yml'),
  yaml.dump(unifiedTestSuite(), {
    lineWidth: 120,
    noRefs: true,
    flowLevel: 4,
    condenseFlow: false
  }),
  'utf8'
);
