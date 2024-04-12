# MongoDB Handshake Tests

## Prose Tests

### Test that the driver accepts an arbitrary auth mechanism

1. Mock the server response in a way that `saslSupportedMechs` array in the `hello` command response contains an
   arbitrary string.

2. Create and connect a `Connection` object that connects to the server that returns the mocked response.

3. Assert that no error is raised.
