package examples;

import com.mongodb.ExplainVerbosity;
import com.mongodb.MongoClient;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.model.AggregateOptions;
import com.mongodb.client.model.BulkWriteOptions;
import com.mongodb.client.model.CountModel;
import com.mongodb.client.model.CountOptions;
import com.mongodb.client.model.DeleteOneModel;
import com.mongodb.client.model.DistinctOptions;
import com.mongodb.client.model.FindModel;
import com.mongodb.client.model.FindOneAndDeleteOptions;
import com.mongodb.client.model.FindOneAndReplaceOptions;
import com.mongodb.client.model.FindOneAndUpdateOptions;
import com.mongodb.client.model.FindOptions;
import com.mongodb.client.model.InsertManyOptions;
import com.mongodb.client.model.InsertOneModel;
import com.mongodb.client.model.UpdateManyModel;
import com.mongodb.client.model.UpdateOptions;
import org.mongodb.Document;

import static java.util.Arrays.asList;
import static java.util.concurrent.TimeUnit.SECONDS;

public class MongoCollectionUsageExample {

    public static void usageExample(MongoCollection<Document> col) {

        // Java's argument passing is very rudimentary compared to most other
        // languages.  No named parameters, no optional parameters, etc.
        // To make it as easy as possible for users to do the simple things simply
        // and the slightly more complex thing not too much more complex,
        // and still abiding by the spec rules for no positional optional parameters
        // the Java driver provides two overloads for each method:
        //
        //  1. An overload with positional parameters for all required model fields
        //  2. An overload with the same positional parameters for all required model
        //     fields, plus an options parameter whose type defines a fluent API for
        //     specifying each optional parameter


        // find

        //   find with no criteria, since criteria is optional
        col.find();

        //   find with criteria, specified in options since...criteria is optional
        col.find(new FindOptions().criteria(new Document("x", 1)));

        //   adding limit is easy once you have options
        col.find(new FindOptions().criteria(new Document("x", 1))
                                  .limit(10));

        //   as are query flags
        col.find(new FindOptions().tailable(true)
                                  .awaitData(true));


        // aggregation

        //   aggregate is just a list of documents
        col.aggregate(asList(new Document("$match", new Document("x", 1)),
                             new Document("$skip", 10)));

        //   and again with a few (non-positional) options.
        col.aggregate(asList(new Document("$match", new Document("x", 1)),
                             new Document("$skip", 10)),
                      new AggregateOptions().allowDiskUse(true)
                                            .maxTime(1, SECONDS));


        // count

        //   count with all required parameters: there are none
        col.count();

        //   count with some optional parameters
        col.count(new CountOptions().criteria(new Document("x", 1))
                                    .maxTime(1, SECONDS));


        // distinct

        col.distinct("y");

        col.distinct("y", new DistinctOptions().criteria(new Document("x", 1)));


        // delete  (no optional parameters for delete, so no options

        col.deleteOne(new Document("x", 1));

        col.deleteMany(new Document("x", 1));


        // insert

        //   insert a single document

        col.insertOne(new Document("x", 1));

        //   insert many documents (well, at least one)
        col.insertMany(asList(new Document("x", 1), new Document("x", 2)));

        //   insert many documents where order does not matter.  Note that even though there
        //   is currently only one option to insertMany, it's still not specified positionally
        //   this leaves room for adding more options down the line without having to add
        //   more overloads
        col.insertMany(asList(new Document("x", 1), new Document("x", 2)),
                       new InsertManyOptions().ordered(false));


        // replaceOne

        col.replaceOne(new Document("x", 1), new Document("x", 2));

        col.replaceOne(new Document("x", 1), new Document("x", 2),
                       new UpdateOptions().upsert(true));


        // update

        col.updateOne(new Document("x", 1), new Document("$set", new Document("x", 2)));

        col.updateOne(new Document("x", 1), new Document("$set", new Document("x", 2)),
                      new UpdateOptions().upsert(true));

        col.updateMany(new Document("x", 1), new Document("$set", new Document("x", 2)));

        col.updateMany(new Document("x", 1), new Document("$set", new Document("x", 2)),
                       new UpdateOptions().upsert(true));


        // bulkWrite

        // an ordered bulk write (the default)
        col.bulkWrite(asList(new InsertOneModel<>(new Document("x", 1)),
                             new UpdateManyModel<>(new Document("x", 1),
                                                   new Document("$set", new Document("x", 2))),
                             new DeleteOneModel<>(new Document("x", 1))));

        // an unordered bulk write (specified as an option)
        col.bulkWrite(asList(new InsertOneModel<>(new Document("x", 1)),
                             new UpdateManyModel<>(new Document("x", 1),
                                                   new Document("$set", new Document("x", 2))),
                             new DeleteOneModel<>(new Document("x", 1))),
                      new BulkWriteOptions().ordered(false));


        // findOneAndDelete

        //   just the query
        col.findOneAndDelete(new Document("x", 1));

        //   query plus optional projection
        col.findOneAndDelete(new Document("x", 1),
                             new FindOneAndDeleteOptions().projection(new Document("y", 1)));


        // findOneAndReplace

        //   query and replacement
        col.findOneAndReplace(new Document("x", 1), new Document("_id", 3).append("x", 2));

        //   query and replacement and optional returnReplaced (note we are changing this to returnOriginal)
        col.findOneAndReplace(new Document("x", 1), new Document("_id", 3).append("x", 2),
                              new FindOneAndReplaceOptions().returnDocument(ReturnDocument.after));


        // findOneAndUpdate

        //   query and update
        col.findOneAndUpdate(new Document("x", 1), new Document("$set", new Document("x", 2)));

        //   query and update and optional returnUpdated (note we are changing this to returnOriginal)
        col.findOneAndUpdate(new Document("x", 1), new Document("$set", new Document("x", 2)),
                             new FindOneAndUpdateOptions().returnDocument(ReturnDocument.after));


        // explain.  note that because there is just a single explain method, we can't use the
        // "required positional parameters plus options" strategy of above.  Instead we have to
        // resort to Model classes that encapsulate the required and optional parameters

        //   explain a count.  note the use of CountModel
        col.explain(new CountModel(new CountOptions().criteria(new Document("x", 1))),
                    ExplainVerbosity.QUERY_PLANNER);

        //   explain a find.  note the use of FindModel
        col.explain(new FindModel(new FindOptions().criteria(new Document("x", 1))),
                    ExplainVerbosity.ALL_PLANS_EXECUTIONS);
    }

    public static void main(String[] args) {
        MongoClient client = new MongoClient();
        usageExample(client.getDatabase("test").getCollection("test"));
    }
}
