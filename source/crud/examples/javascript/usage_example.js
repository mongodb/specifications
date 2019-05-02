

// find

	col.find({x:1});

	col.find({x:1}).limit(10);

	col.find({x:1}, {limit: 10});


// aggregate

	col.aggregate([
			{$match : {x: 1}},
			{$skip: 10}
		]);

	col.aggregate()
		.match({x:1})
		.skip(20);


// count

	col.count({x: 1});

	col.count({x: 1}, {maxTimeMS: 2000});

	
// distinct

	col.distinct("y", {x: 1});

// delete

	col.deleteOne({x: 1});

	col.deleteMany({x: 1});

// insert

	col.insertOne({x: 1});

	col.insertMany([{x: 1}, {x: 2}], {continueOnError: true});


// replaceOne

	col.replaceOne({x: 1}, {x: 2}, {upsert: true});


// update

	col.updateOne({x: 1}, {$set: {x: 2}}, {upsert: true});
	col.updateOne({x: 1}, [{$set: {x: 2}}, {upsert: true}]);

	col.updateMany({x: 1}, {$set: {x: 2}}, {upsert: true});
	col.updateMany({x: 1}, [{$set: {x: 2}}, {upsert: true}]);


// bulkWrite

	col.bulkWrite([
			{ insertOne: {document: {x: 1}} },
			{ updateMany: {filter: {x: 1}, update: {$set: {x: 2}} },
			{ deleteOne: {filter: {x: 1}} }
		],
		{ ordered: false }
	);


// findOneAndDelete

	col.findOneAndDelete({x: 1}, {projection: {y: 1, _id: 0}});


// findOneAndReplace

	col.findOneAndReplace({x: 1}, {x: 2}, {returnDocument: ReturnDocument.after});


// findOneAndUpdate

	col.findOneAndUpdate({x: 1}, {$set: {x: 2}}, {returnDocument: ReturnDocument.after});
	col.findOneAndUpdate({x: 1}, [{$set: {x: 2}}], {returnDocument: ReturnDocument.after});
