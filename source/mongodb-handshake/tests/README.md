# MongoDB Handshake Tests

## Prose Tests

### Test that the driver accepts an arbitrary auth mechanism

1. Mock the server response in a way that `hello` command response contains an arbitrary string in the `saslSupportedMechs` attribute.

2. Connect to the server.

3. Assert that no error is raised.
