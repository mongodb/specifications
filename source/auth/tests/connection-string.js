

describe("connection string", function() {
	it("should use the default source and mechanism", function() {
		var url = parse("mongodb://user:password@localhost");

		assert.equal(url.credential.source, "admin");
		assert.equal(url.credential.mechanism, null);
	});

	it("should use the database when no authSource is specified", function() {
		var url = parse("mongodb://user:password@localhost/foo");

		assert.equal(url.credential.source, "foo");
	});

	it("should use the authSource when specified", function() {
		var url = parse("mongodb://user:password@localhost/foo/?authSource=bar");

		assert.equal(url.credential.source, "bar");
	});

	it("should recognize an empty password", function() {
		var url = parse("mongodb://user:@localhost");

		assert.equal(url.credential.username, "user");
		assert.equal(url.credential.password, "");
	});

	it("should recognize no password", function() {
		var url = parse("mongodb://user@localhost");

		assert.equal(url.credential.username, "user");
		assert.isNull(url.credential.password);
	});

	it("should recognize no password", function() {
		var url = parse("mongodb://user@localhost");

		assert.equal(url.credential.username, "user");
		assert.isNull(url.credential.password);
	});

	it("should recognize a url escaped character in the username", function() {
		var url = parse("mongodb://user%40DOMAIN.COM:password@localhost");

		assert.equal(url.credential.username, "user@DOMAIN.COM");
	});

	describe("GSSAPI", function() {
		it("should recognize the mechanism", function() {
			var url = parse("mongodb://user@localhost/?authMechanism=GSSAPI");

			assert.equal(url.credential.mechanism, "GSSAPI");
		});

		it("should use $external as the source", function() {
			var url = parse("mongodb://user%40DOMAIN.COM:password@localhost/?authMechanism=GSSAPI");

			assert.equal(url.credential.source, "$external");
		});

		it("should use $external as the source when a database is specified", function() {
			var url = parse("mongodb://user%40DOMAIN.COM:password@localhost/foo/?authMechanism=GSSAPI");

			assert.equal(url.credential.source, "$external");
		});

		it("should throw an exception when an authSource is specified other than $external", function() {
			assert.throws(function() {
				parse("mongodb://user%40DOMAIN.COM:password@localhost/foo/?authMechanism=GSSAPI&authSource=bar");
			});
		});

		it("should throw an exception when an authMechanism is specified with no username", function() {
			assert.throws(function() {
				parse("mongodb://localhost/?authMechanism=GSSAPI");
			});
		});

		it("should accept generic mechanism property", function() {
			var url = parse("mongodb://user%40DOMAIN.COM:password@localhost/?authMechanism=GSSAPI&authMechanismProperties=SERVICE_NAME:other,CANONICALIZE_HOST_NAME:true");

			assert.equal(url.credential.mechanismProperties["SERVICE_NAME"], "other");
			assert.equal(url.credential.mechanismProperties["CANONICALIZE_HOST_NAME"], "true");
		});

		it("should accept legacy gssapiServiceName", function() {
			var url = parse("mongodb://user%40DOMAIN.COM:password@localhost/?authMechanism=GSSAPI&gssapiServiceName=other");

			assert.equal(url.credential.mechanismProperties["SERVICE_NAME"], "other");
		});
	});

	describe("MONGODB-CR", function() {
		it("should recognize the mechanism", function() {
			var url = parse("mongodb://user:pass@localhost/?authMechanism=MONGODB-CR");

			assert.equal(url.credential.mechanism, "MONGODB-CR");
		});
		it("should throw an exception when an authMechanism is specified with no username", function() {
			assert.throws(function() {
				parse("mongodb://localhost/?authMechanism=MONGODB-CR");
			});
		});
	});

	describe("MONGODB-X509", function() {
		it("should use $external as the source", function() {
			var url = parse("mongodb://CN%3DmyName%2COU%3DmyOrgUnit%2CO%3DmyOrg%2CL%3DmyLocality%2CST%3DmyState%2CC%3DmyCountry@localhost/?authMechanism=MONGODB-X509");

			assert.equal(url.credential.source, "$external");
		});

		it("should use $external as the source when a database is specified", function() {
			var url = parse("mongodb://CN%3DmyName%2COU%3DmyOrgUnit%2CO%3DmyOrg%2CL%3DmyLocality%2CST%3DmyState%2CC%3DmyCountry@localhost/foo/?authMechanism=MONGODB-X509");

			assert.equal(url.credential.source, "$external");
		});

		it("should throw an exception when an authSource is specified other than $external", function() {
			assert.throws(function() {
				parse("mongodb://CN%3DmyName%2COU%3DmyOrgUnit%2CO%3DmyOrg%2CL%3DmyLocality%2CST%3DmyState%2CC%3DmyCountry@localhost/foo/?authMechanism=MONGODB-X509&authSource=bar");
			});
		});

		it("should recognize the mechanism", function() {
			var url = parse("mongodb://CN%3DmyName%2COU%3DmyOrgUnit%2CO%3DmyOrg%2CL%3DmyLocality%2CST%3DmyState%2CC%3DmyCountry@localhost/?authMechanism=MONGODB-X509");

			assert.equal(url.credential.mechanism, "MONGODB-X509");
		});

		it("should recognize the mechanism with no username", function() {
			var url = parse("mongodb://localhost/?authMechanism=MONGODB-X509");

			assert.equal(url.credential.mechanism, "MONGODB-X509");
			assert.equal(url.credential.username, null);
		});

		it("should recognize the encoded username", function() {
			var url = parse("mongodb://CN%3DmyName%2COU%3DmyOrgUnit%2CO%3DmyOrg%2CL%3DmyLocality%2CST%3DmyState%2CC%3DmyCountry@localhost/?authMechanism=MONGODB-X509");

			assert.equal(url.credential.username, "CN=myName,OU=myOrgUnit,O=myOrg,L=myLocality,ST=myState,C=myCountry");
		});
	});

	describe("PLAIN", function() {
		it("should recognize the mechanism", function() {
			var url = parse("mongodb://user:password@localhost/?authMechanism=PLAIN");

			assert.equal(url.credential.mechanism, "PLAIN");
		});

		it("should throw an exception when an authMechanism is specified with no username", function() {
			assert.throws(function() {
				parse("mongodb://localhost/?authMechanism=PLAIN");
			});
		});
	});

	describe("SCRAM-SHA-1", function() {
		it("should recognize the mechanism", function() {
			var url = parse("mongodb://user:password@localhost/?authMechanism=SCRAM-SHA-1");

			assert.equal(url.credential.mechanism, "SCRAM-SHA-1");
		});

		it("should throw an exception when an authMechanism is specified with no username", function() {
			assert.throws(function() {
				parse("mongodb://localhost/?authMechanism=SCRAM-SHA-1");
			});
		});
	});
});

