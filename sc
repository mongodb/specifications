DIR0=source/server-discovery-and-monitoring/tests/rs
DIR1=/Users/preston.vasquez/Developer/mongo-go-driver/testdata/server-discovery-and-monitoring/rs

cp $DIR0/electionId_precedence_setVersion.json $DIR1/electionId_precedence_setVersion.json
cp $DIR0/electionId_precedence_setVersion.yml $DIR1/electionId_precedence_setVersion.yml

cp $DIR0/null_election_id-pre-6.0.json $DIR1/null_election_id-pre-6.0.json
cp $DIR0/null_election_id-pre-6.0.yml $DIR1/null_election_id-pre-6.0.yml

cp $DIR0/null_election_id.json $DIR1/null_election_id.json
cp $DIR0/null_election_id.yml $DIR1/null_election_id.yml

cp $DIR0/secondary_ignore_ok_0-pre-6.0.json $DIR1/secondary_ignore_ok_0-pre-6.0.json
cp $DIR0/secondary_ignore_ok_0-pre-6.0.yml $DIR1/secondary_ignore_ok_0-pre-6.0.yml

cp $DIR0/set_version_can_rollback.json $DIR1/set_version_can_rollback.json
cp $DIR0/set_version_can_rollback.yml $DIR1/set_version_can_rollback.yml
