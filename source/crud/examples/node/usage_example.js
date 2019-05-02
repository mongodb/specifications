// Idiomatic Javascript is to make required arguments parameters and the rest be options in a dictionary.
// So if function A requires the arguments B and C but has options D and E it would be like this.
//
// A(B, C, {D:1, E:0}, function(err, r) {})

// find

  col.find({x:1})
    .limit(10)
    .toArray(function(err, docs) {
  });

  col.find()
    .skip(20)
    .awaitData(true)
    .tailable(true)
    .toArray(function(err, docs) {
  });

// aggregate

  col.aggregate([
      { $match : { x: 1 } },
      { $skip: 10 }    
    ]).toArray(function(err, docs) {
  });

// count

  col.count({ x: 1 }, {maxTimeMS:2000}, function(err, count) {
  });


// distinct

  col.distinct("y", {criteria: { x: 1 }}, function(err, r) {});

// delete

  col.deleteOne({ x: 1 }, function(err, r) {});

  col.deleteOne({ x: 1 }, function(err, r) {});

  col.deleteMany({ x: 1 }, function(err, r) {});


// insert

  col.insertOne({ x: 1 }, function(err, r) {});

  col.insertMany([
      { x: 1 },
      { x: 2 },
    ], { ordered : true }, function(err, r) {});


// replaceOne

  col.replaceOne({ x: 1 }, { x: 2 }, {upsert: true}, function(err, r) {});

// update

  col.updateOne({ x: 1 }, { $set: { x: 2 } }, { upsert: true}, function(err, r) {});
  col.updateOne({ x: 1 }, [{ $set: { x: 2 } }], { upsert: true}, function(err, r) {});

// bulkWrite

  col.bulkWrite([
    { 
      insertOne: { x: 1 } 
    },
    { 
      updateMany: { 
        criteria: { x: 1 }, 
        update: { $set: { x: 2 } }
      }
    },
    { 
      deleteOne: {
        criteria: { x: 1 }
      }
    }], { ordered: false }, function(err, r) {});

// findOneAndDelete

  col.findOneAndDelete({ x: 1 }, {
    projection: { y: 1, _id: 0 },
  }, function(err, r) {});


// findOneAndReplace

  col.findOneAndReplace({ x: 1 }, { x: 2 }, {
    returnDocument: ReturnDocument.after
  }, function(err, r) {});

// findOneAndUpdate

  col.findOneAndUpdate({ x: 1 }, { $set: { x: 2 } }, {
    returnDocument: ReturnDocument.after
  }, function(err, r) {});
  col.findOneAndUpdate({ x: 1 }, [{ $set: { x: 2 } }], {
    returnDocument: ReturnDocument.after
  }, function(err, r) {});
