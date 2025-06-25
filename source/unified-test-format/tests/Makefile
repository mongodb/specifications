.PHONY: all \
	atlas-data-lake \
	auth \
	change-streams \
	client-side-encryption \
	client-side-operations-timeout \
	collection-management \
	command-logging-and-monitoring \
	command-logging-and-monitoring/logging \
	command-logging-and-monitoring/monitoring \
	connection-monitoring-and-pooling \
	connection-monitoring-and-pooling/logging \
	crud \
	gridfs \
	index-management \
	load-balancers \
	read-write-concern \
	retryable-reads \
	retryable-writes \
	run-command \
	server-discovery-and-monitoring \
	server-selection \
	server-selection/logging \
	sessions \
	transactions-convenient-api \
	transactions \
	unified-test-format \
	unified-test-format/invalid \
	unified-test-format/valid-fail \
	unified-test-format/valid-pass \
	versioned-api \
	HAS_AJV

all: atlas-data-lake \
	auth \
	change-streams \
	client-side-encryption \
	client-side-operations-timeout \
	collection-management \
	command-logging-and-monitoring \
	connection-monitoring-and-pooling \
	crud \
	gridfs \
	index-management \
	load-balancers \
	read-write-concern \
	retryable-reads \
	retryable-writes \
	run-command \
	server-discovery-and-monitoring \
	server-selection \
	sessions \
	transactions-convenient-api \
	transactions \
	unified-test-format \
	versioned-api

# Keep specifications sorted alphabetically
# When adding a new specification, remember to add it to the all and .PHONY targets above
# For specifications that contain multiple test folders, create a target for each folder
# in addition to a target for the specification itself
atlas-data-lake: HAS_AJV
	@./check-files.sh valid ../../atlas-data-lake-testing/tests/unified/*.yml

auth: HAS_AJV
	@./check-files.sh valid ../../auth/tests/unified/*.yml

change-streams: HAS_AJV
	@./check-files.sh valid ../../change-streams/tests/unified/*.yml

client-side-encryption: HAS_AJV
	@./check-files.sh valid ../../client-side-encryption/tests/unified/*.yml

client-side-operations-timeout: HAS_AJV
	@./check-files.sh valid ../../client-side-operations-timeout/tests/*.yml

collection-management: HAS_AJV
	@./check-files.sh valid ../../collection-management/tests/*.yml

command-logging-and-monitoring: command-logging-and-monitoring/logging command-logging-and-monitoring/monitoring

command-logging-and-monitoring/logging: HAS_AJV
	@./check-files.sh valid ../../command-logging-and-monitoring/tests/logging/*.yml

command-logging-and-monitoring/monitoring: HAS_AJV
	@./check-files.sh valid ../../command-logging-and-monitoring/tests/monitoring/*.yml

connection-monitoring-and-pooling: connection-monitoring-and-pooling/logging

connection-monitoring-and-pooling/logging: HAS_AJV
	@./check-files.sh valid ../../connection-monitoring-and-pooling/tests/logging/*.yml

crud: HAS_AJV
	@./check-files.sh valid ../../crud/tests/unified/*.yml

gridfs: HAS_AJV
	@./check-files.sh valid ../../gridfs/tests/*.yml

index-management: HAS_AJV
	@./check-files.sh valid ../../index-management/tests/*.yml

load-balancers: HAS_AJV
	@./check-files.sh valid ../../load-balancers/tests/*.yml

read-write-concern: HAS_AJV
	@./check-files.sh valid ../../read-write-concern/tests/operation/*.yml

retryable-reads: HAS_AJV
	@./check-files.sh valid ../../retryable-reads/tests/unified/*.yml

retryable-writes: HAS_AJV
	@./check-files.sh valid ../../retryable-writes/tests/unified/*.yml

run-command: HAS_AJV
	@./check-files.sh valid ../../run-command/tests/unified/*.yml

server-discovery-and-monitoring: HAS_AJV
	@./check-files.sh valid ../../server-discovery-and-monitoring/tests/unified/*.yml

server-selection: server-selection/logging

server-selection/logging: HAS_AJV
	@./check-files.sh valid ../../server-selection/tests/logging/*.yml

sessions: HAS_AJV
	@./check-files.sh valid ../../sessions/tests/*.yml

transactions-convenient-api: HAS_AJV
	@./check-files.sh valid ../../transactions-convenient-api/tests/unified/*.yml

transactions: HAS_AJV
	@./check-files.sh valid ../../transactions/tests/unified/*.yml

unified-test-format: unified-test-format/invalid unified-test-format/valid-fail unified-test-format/valid-pass

unified-test-format/invalid: HAS_AJV
	@# Redirect stdout to hide expected validation errors
	@./check-files.sh invalid invalid/*.yml > /dev/null && echo "invalid/*.yml passed test"

unified-test-format/valid-fail: HAS_AJV
	@./check-files.sh valid valid-fail/*.yml

unified-test-format/valid-pass: HAS_AJV
	@./check-files.sh valid valid-pass/*.yml

versioned-api: HAS_AJV
	@./check-files.sh valid ../../versioned-api/tests/*.yml

HAS_AJV:
	@if ! command -v ajv > /dev/null; then                \
	    echo 'Error: need "npm install -g ajv-cli"' 1>&2; \
	    exit 1;                                           \
	fi
