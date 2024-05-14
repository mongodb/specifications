# Driver Mantras

When developing specifications -- and the drivers themselves -- we follow the following principles:

### Strive to be idiomatic, but favor consistency

Drivers attempt to provide the easiest way to work with MongoDB in a given language ecosystem, while specifications
attempt to provide a consistent behavior and experience across all languages. Drivers should strive to be as idiomatic
as possible while meeting the specification and staying true to the original intent.

### No Knobs

Too many choices stress out users. Whenever possible, we aim to minimize the number of configuration options exposed to
users. In particular, if a typical user would have no idea how to choose a correct value, we pick a good default instead
of adding a knob.

### Topology agnostic

Users test and deploy against different topologies or might scale up from replica sets to sharded clusters. Applications
should never need to use the driver differently based on topology type.

### Where possible, depend on server to return errors

The features available to users depend on a server's version, topology, storage engine and configuration. So that
drivers don't need to code and test all possible variations, and to maximize forward compatibility, always let users
attempt operations and let the server error when it can't comply. Exceptions should be rare: for cases where the server
might not error and correctness is at stake.

### Minimize administrative helpers

Administrative helpers are methods for admin tasks, like user creation. These are rarely used and have maintenance costs
as the server changes the administrative API. Don't create administrative helpers; let users rely on "RunCommand" for
administrative commands.

### Check wire version, not server version

When determining server capabilities within the driver, rely only on the maxWireVersion in the hello response, not on
the X.Y.Z server version. An exception is testing server development releases, as the server bumps wire version early
and then continues to add features until the GA.

### When in doubt, use "MUST" not "SHOULD" in specs

Specs guide our work. While there are occasionally valid technical reasons for drivers to differ in their behavior,
avoid encouraging it with a wishy-washy "SHOULD" instead of a more assertive "MUST".

### Defy augury

While we have some idea of what the server will do in the future, don't design features with those expectations in mind.
Design and implement based on what is expected in the next release.

Case Study: In designing OP_MSG, we held off on designing support for Document Sequences in Replies in drivers until the
server would support it. We subsequently decided not to implement that feature in the server.

### The best way to see what the server does is to test it

For any unusual case, relying on documentation or anecdote to anticipate the server's behavior in different
versions/topologies/etc. is error-prone. The best way to check the server's behavior is to use a driver or the shell and
test it directly.

### Drivers follow semantic versioning

Drivers should follow X.Y.Z versioning, where breaking API changes require a bump to X. See
[semver.org](https://semver.org/) for more.

### Backward breaking behavior changes and semver

Backward breaking behavior changes can be more dangerous and disruptive than backward breaking API changes. When
thinking about the implications of a behavior change, ask yourself what could happen if a user upgraded your library
without carefully reading the changelog and/or adequately testing the change.
