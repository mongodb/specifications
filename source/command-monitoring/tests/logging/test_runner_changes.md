## required drivers changes:
- client entities can now have `observeLogMessages`, which is an object with key/value pairs indicating component name and corresponding max verbosity levels. the test runner should use these to configure logging infrastructure to capture messages using these settings
	- for drivers with a global rather than per-client logger they will need to include a unique client ID in each message to allow filtering messages for each client entity.  (probably we should just make all drivers do this since it’s useful.)
- a component name will always be one of the component names we define in the logging spec (e.g. `command` or `sdam` ). 
	- the tests so far only use `command`
	- for convenience in Rust when deserializing the JSON I map this to the Rust-specific names we’ll use for these components like `mongodb::command`
- the value for component will always be one of the log levels we define in the logging spec. drivers who don’t have all those levels will want to convert these as needed to the equivalent level for the purpose of assertions
	- the tests so far only use `debug` 
- similar to `expectEvents` and `expectedEventsForClient`, a test can now have `expectLogMessages` which is an array of `expectedLogMessagesForClient` objects (one per entity) that contain the client entity ID as well as an array of one or more `expectedLogMessage`s.
- each `expectedLogMessage` has a `component` and a `level` (which can take on the same values for components/levels as described above),  along with a `data` object containing arbitrary key-value pairs 
- drivers should match the actual messages with expected messages after running all operations
	- component and level should be exact equality matches 
	- data should be matched with the actual log message data as a root document (so extra fields are allowed) 
	- this is going to require drivers doing unstructured logging to design their logging internals such that data is first gathered into a structured form (like a document or hash map) that can be intercepted in tests and used for assertions, and is then later string-ified to output to the user 

## todos / notes
- it might seem funny that I check the command/reply are strings, but I think we probably need to do it that way where drivers serialize them to extJSON strings before assertion time, so we can test truncation works as required. 
-  we should test serverConnectionId is present on 4.2+, and not present < 4.2. I skipped this because Rust doesn't expose that yet. need to add
 -  should test serviceId is included when in load balancer mode
* for drivers w/ operationIds, add a test that is included when appropriate
