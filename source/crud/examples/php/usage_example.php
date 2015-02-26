<?php

// find

$collection->find(
    // Optional criteria param, which we allow as the first positional argument for BC
    ['x' => 1],
    // Optional named params in an associative array (BC break, projection in 1.x)
    ['limit' => 10]
);

$collection->find(
    // Optional criteria param, which we allow as the first positional argument for BC
    [],
    // Optional named params in an associative array (BC break, projection in 1.x)
    [
        'skip' => 20,
        'tailable' => true,
        'awaitData' => true,
    ]
);


// aggregate

$collection->aggregate(
    // Required pipeline param
    [
        ['$match' => ['x' => 1]],
        ['$skip' => 10],
    ],
    // Optional named params in an associative array
    ['allowDiskUse' => true]
);


// count

$collection->count(
    // Optional criteria param, which we allow as the first positional argument for BC
    ['x' => 1],
    // Optional named params in an associative array
    ['maxTimeMS' => 2000]
);

$collection->count(
    // Optional criteria param, which we allow as the first positional argument for BC
    [],
    // Optional named params in an associative array
    ['maxTimeMS' => 2000]
);


// distinct

$collection->distinct(
    // Required field param
    'y',
    // Optional named params in an associative array (BC break, criteria in 1.x)
    [
        'criteria' => ['x' => 1],
        'maxTimeMS' => 2000,
    ]
);


// delete

$collection->deleteOne([]); // First position argument is required criteria
$collection->deleteOne(['x' => 1]);
$collection->deleteMany(['x' => 1]);


// insert

$collection->insertOne(['x' => 1]);

$collection->insertMany(
    // Required documents param (array of documents)
    [
        ['x' => 1],
        ['x' => 2],
    ],
    // Optional named params in an associative array
    ['ordered' => true]
);

$collection->insertOne(
    // Required document param
    ['x' => 1],
    // Optional named params in an associative array (allow mixing of write concern options?)
    ['w' => 'majority']
);

$collection->insertMany(
    // Required documents param (array of documents)
    [
        ['x' => 1],
        ['x' => 2],
    ],
    // Optional named params in an associative array (allow mixing of write concern options?)
    [
        'ordered' => true,
        'w' => 'majority',
    ]
);


// replaceOne

$collection->replaceOne(
    ['x' => 1],
    ['x' => 2],
    ['upsert' => true]
);


// update

$collection->updateOne(
    ['x' => 1],
    ['$set' => ['x' => 2]],
    ['upsert' => true]
);

$collection->updateMany(
    ['x' => 1],
    ['$set' => ['x' => 2]],
    ['upsert' => true]
);


// bulkWrite

$collection->bulkWrite(
    // Required writes param (an array of operations)
    [
        // Like explain(), operations identified by single key
        [
            'insertOne' => [
                ['x' => 1]
            ],
        ],
        [
            'updateMany' => [
                ['x' => 1],
                ['$set' => ['x' => 2]],
            ],
        ],
        [
            'updateOne' => [
                ['x' => 3],
                ['$set' => ['x' => 4]],
                // Optional params are still permitted
                ['upsert' => true],
            ],
        ],
        [
            'deleteOne' => [
                ['x' => 1],
            ],
        ],
        [
            'deleteMany' => [
                // Required arguments must still be specified
                [], 
            ],
        ],
    ],
    // Optional named params in an associative array
    ['ordered' => false]
);


// findOneAndDelete

$collection->findOneAndDelete(
    // Required criteria param
    ['x' => 1],
    // Optional named params in an associative array
    [
        'projection' => ['y' => 1, '_id' => 0],
    ]
);


// findOneAndReplace

$collection->findOneAndReplace(
    // Required criteria param
    ['x' => 1],
    // Required replacement param
    ['x' => 2],
    // Optional named params in an associative array
    ['returnDocument' => ReturnDocument::Before]
);


// findOneAndUpdate


$collection->findOneAndUpdate(
    // Required criteria param
    ['x' => 1],
    // Required update param
    ['$set' => ['x' => 2]],
    // Optional named params in an associative array
    ['returnDocument' => ReturnDocument::After]
);


// explain

$collection->explain(
    // Required command param
    [
        // Single key identifies the command
        'count' => [
            // Optional criteria param (in first position for consistency with method)
            ['x' => 1],
            // Optional named params in an associative array
            ['maxTimeMS' => 2000],
        ],
    ]
);

$collection->explain(
    // Required command param
    [
        // Single key identifies the command
        'updateOne' => [
            // Required criteria param
            ['x' => 1],
            // Required update param
            ['$inc' => ['x' => 2]],
            // Optional named params in an associative array
            ['upsert' => false],
        ],
    ]
);
