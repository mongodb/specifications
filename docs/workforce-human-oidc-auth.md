# Requirements for Client Applications implementing Workforce (Human) OIDC Auth For MongoDB

# Overview

## Abstract

MongoDB offers OpenID Connect (OIDC) authentication and authorization for database users. OIDC auth in clients generally
falls into one of two categories: either Workflow OIDC targeting programmatic users, which is
[fully specified here](https://github.com/mongodb/specifications/blob/master/source/auth/auth.md#mongodb-oidc) and does
not involve user interaction, or Workforce OIDC targeting human users, which authenticate explicitly through means such
as browsers.

## Audience

This document is intended for authors and maintainers of MongoDB client applications that implement Workforce OIDC
authentication, or those who wish to understand existing implementations of it. This document does *not* describe the
server implementation of OIDC, nor the details of OIDC protocol interactions that are part of external standards and
generally implemented through the use of a third-party library.

## Meta

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Token acquisition flows

Currently, all workforce OIDC clients in MongoDB support one or two mechanisms for acquiring OIDC tokens:

- Authorization Code Flow with PKCE (short: Auth Code, PKCE is pronounced “pixie”)
- Device Authorization Grant (short: Device Auth)

Auth Code Flow is generally the preferred mechanism. If an application decides to only support one of these flows, that
should be the typical choice. If an application supports both flows, it MAY default to Auth Code Flow and fall back to
Device Auth only if

- The former is unavailable under specific circumstances, which are described in the Auth Code Flow section; and
- The user has explicitly indicated that Device Auth is enabled for this connection attempt.

In both of these cases, the general chain of events is as follows:

1. The user passes a connection string to the client application and indicates (possibly through said connection string)
    that they desire to use `MONGODB-OIDC` as their authentication mechanism.
2. The application connects to the MongoDB endpoint and asks it for information about the Identity Provider (IdP)[^1] it
    is supposed to authenticate with. If there was a username in the connection string, the application sends that as
    well.
3. The MongoDB endpoint responds with information about the IdP, in the form of an `issuer` URL identifying the IdP and
    other metadata about it.
4. The application looks up the public metadata document for the IdP, which includes information about user-facing URL
    endpoints.
5. The application composes a URL based on those endpoints and presents it to the user in some form (the details depend
    on the exact flow chosen).
6. The user visits that URL, which can result in any number of steps to authenticate the user.
7. The application receives a token from the IdP (the details again depend on the exact flow chosen).
8. The application presents this token to the MongoDB endpoint.

Since in these steps the client application performs actions depending on information supplied by external sources, this
document specifies mechanisms that help ensure that these actions are carried out securely. MongoDB clients are “public
clients” in the sense of the OIDC specs (i.e. they do not possess a shared secret with the Identity Provider), and must
behave accordingly.

Since these steps require the involvement of a human being, the application should be set up to gracefully handle
timeouts and provide the user with a way to abort the connection attempt.

# General requirements

An application implementing workforce OIDC needs to generally comply with OpenID and OAuth 2.0 standards.

In particular:

- Any HTTP calls made to non-local servers MUST be made using HTTPS.
- IdP metadata discovery MUST be implemented as described in [RFC8414](https://datatracker.ietf.org/doc/html/rfc8414).

Using a well-tested and standards-compliant third-party library for core OIDC logic for the respective ecosystem is
highly recommended. If this is not possible, implementers need to pay special attention to the specifications referenced
in this document.

## Token management

After a successful authentication, applications SHOULD periodically attempt to use the OIDC token refresh mechanism in
order to exchange the access token it uses for a fresh one. The refresh interval SHOULD be determined by the token
expiry time indicated by the Identity Provider. If the refresh attempt fails, the application MAY ask or suggest the
user to re-authenticate from scratch, even if the currently used access token has not expired yet.

Under normal circumstances, the application provides an access token received from the Identity Provider to the driver.
The application SHOULD provide a toggle to users that can be used to indicate that it should use the ID token, rather
than the access token, in its place.[^2]

## OIDC Scopes

The initial request to the IdP involves specifying the `scope` parameter. This is a space-separated unordered list of
strings which contains:

- The scopes listed in the `requestScopes` field of the IdP response from the MongoDB endpoint, and
- The `openid` and `offline_access` scopes[^3]. If the IdP metadata document contains a `scopes_supported` field, and
    this field does not list one of these scopes, then the respective scope SHOULD NOT be added to the `scope`
    parameter.

# Authorization Code Flow

In this flow, the client application uses a local HTTP server to receive a response from the Identity Provider, as
described in [RFC8252](https://datatracker.ietf.org/doc/html/rfc8252).[^4] The application follows these steps:

1. Generate a code challenge for PKCE using cryptographically random data, as described in
    [RFC7636](https://datatracker.ietf.org/doc/html/rfc7636).
2. Launch a local HTTP server. The default (incoming) redirect URL for MongoDB applications is
    `http://localhost:27097/redirect`, which MAY be configurable. If the application allows configuring the URL, the
    port MAY be specified as `0` to allow listening on an arbitrary port. The application listens on the host and port
    listed in the URL. The application MUST listen on all unique addresses that the hostname resolves to through
    `getaddrinfo()`, and MUST listen on the same port in all cases. If listening on any address fails, or
    `getaddrinfo()` did not return any addresses, it must abort this process and the application MAY fall back to
    Device Auth.
    1. To preserve privacy, pages served from this local HTTP server MUST NOT reference external resources directly.
        They MAY provide external links that require user interaction.
    2. The HTTP server SHOULD set default headers of `Content-Security-Policy: default-src 'self'` and
        `Referrer-Policy: no-referrer`, or similarly restrictive defaults.
3. Compose the URL for Auth Code Flow, using the code challenge generated earlier and the redirect URL from the
    previous step, with the port replaced with the actual port if it was specified as `0`.
    1. The application MUST add a `state` parameter containing cryptographically random data
        ([RFC6749](https://datatracker.ietf.org/doc/html/rfc6749#section-4.1.1) specifies this as optional but
        recommended).
    2. The application SHOULD allow the user to indicate that it should add a `nonce` parameter containing
        cryptographically random data to the authentication request, as defined in the OpenID Connect specification,
        which is then later embedded in the ID token itself. This option SHOULD be on-by-default. (Some Identity
        Providers may effectively require a `nonce` option, but since it is an OpenID Connect feature and not an OAuth
        2.0 feature, we allow users to disable this if their Identity Provider does not support it.)
4. The application SHOULD, instead of directly presenting the URL from the previous step to the user, register that URL
    as an outgoing HTTP 307 redirect from the local HTTP server. The redirect base URL SHOULD contain a piece of
    cryptographically random data. The advantages of this approach are that:
    1. The application can ensure that the URL that is passed to the browser in the next step does not contain special
        characters (other than the typical `/` and `:` present in URLs) which would need to be escaped when opening a
        browser through a shell command.
    2. It allows tracking whether the URL has been accessed, i.e. get a definite confirmation of whether the user
        successfully opened it in a browser.
5. Open a browser pointing at that URL, or instruct the user to do so. The former approach is preferred. If opening a
    browser fails, the application MAY fall back to Device Auth.
6. Wait until one of the following events occurs:
    1. The local outgoing redirect URL is accessed (if any).
    2. Opening the browser fails.
    3. A timeout occurs or the connection attempt is aborted.
7. Wait until the incoming redirect URL is accessed in a valid way, i.e. using GET or POST with the correct `state`
    parameter and without an `error` parameter. If the incoming redirect URL is accessed with a mismatching `state`
    parameter or the `error` parameter is set, the application SHOULD display a helpful error page. If an `iss`
    parameter is present, it MUST be validated according to [RFC9207](https://datatracker.ietf.org/doc/html/rfc9207),
    i.e. compare equal to the `issuer` string in the issuer metadata document. Subsequent requests to the incoming
    redirect URL should be rejected.
    1. If error parameters such as `error`, `error_description` and/or `error_uri` are displayed to the user, they MUST
        be validated to match the `NQSCHAR` definition of [RFC6749](https://datatracker.ietf.org/doc/html/rfc6749) (and
        in the case of `error_uri`, a valid URI) before doing so, and they MUST be escaped as appropriate for the
        chosen display format.
8. The application MUST redirect from the incoming redirect URL to a different URL on the same local HTTP server as a
    HTTP 303 redirect, removing all query parameters and/or the request body. The target page SHOULD indicate
    successful authentication to the Identity Provider, and SHOULD clarify that the user is not authenticated with the
    MongoDB endpoint yet. It MAY be updated once the application successfully authenticates against the MongoDB
    endpoint to reflect that.
9. Stop listening on and close the local HTTP server. As browsers may keep lingering open connections, the application
    SHOULD ensure that these connections do not prevent the application from progressing to the next step (i.e. do not
    block closing the server).
10. Verify the parameters it received against the initial PKCE code challenge.
11. Perform a request to the OIDC token endpoint using the code received from the IdP on the incoming redirect URL.
12. Provide the token it received from the token endpoint to the MongoDB driver.

The developer tools team owns example templates for the local HTTP server at
[https://github.com/mongodb-js/devtools-shared/tree/main/packages/oidc-http-server-pages](https://github.com/mongodb-js/devtools-shared/tree/main/packages/oidc-http-server-pages),
and publishes templates that can be accessed at e.g.
[https://unpkg.com/@mongodb-js/oidc-http-server-pages/dist/templates.gz](https://unpkg.com/@mongodb-js/oidc-http-server-pages/dist/templates.gz).

# Device Auth Grant

This flow is optional, and MUST NOT be used unless either:

- The application has been unable to open a browser locally (e.g. in headless environments), or unable to listen on a
    local HTTP endpoint, and the user has explicitly indicated that falling back to this flow is acceptable; or
- The user has explicitly requested this flow.

It is significantly simpler than the Auth Code Flow, but generally considered the less secure one between the two, and
more susceptible to e.g. phishing attacks.

The application follows these steps:

1. Reach out to the IdP device authorization endpoint. This should result in a URL and a “user code”.
2. Present the URL and the user code to the user, expecting the user to open that URL manually (possibly on a different
    device).
3. Repeatedly poll the token endpoint for an access token.
4. Provide the token it received from the token endpoint to the MongoDB driver.

# Diagnostics

It is recommended to log the following events for diagnostic purposes:

- All outgoing HTTP calls, minus sensitive information (e.g. URLs, with search parameter values redacted)
- All inbound HTTP calls, minus sensitive information
- Starting to listen on the local HTTP server, including port and address(es), and whether that was successful or not
- Incoming redirect to the local HTTP server accessed and whether the redirect was accepted or rejected
- Closing of the local HTTP server
- Browser opening and whether it were successful or not
- Acquisition of new tokens from the Identity Provider, and in particular whether an ID token was present or not
- Token refresh attempts and whether they were successful or not

# Appendix: Relevant standards (non-exhaustive)

- [RFC6749](https://datatracker.ietf.org/doc/html/rfc6749): The OAuth 2.0 Authorization Framework
- [RFC6819](https://datatracker.ietf.org/doc/html/rfc6819): OAuth 2.0 Threat Model and Security Considerations
- [RFC7636](https://datatracker.ietf.org/doc/html/rfc7636): Proof Key for Code Exchange by OAuth Public Clients (PKCE)
- [RFC8252](https://datatracker.ietf.org/doc/html/rfc8252): OAuth 2.0 for Native Apps
- [RFC8414](https://datatracker.ietf.org/doc/html/rfc8414): OAuth 2.0 Authorization Server Metadata
- [RFC8628](https://datatracker.ietf.org/doc/html/rfc8628): OAuth 2.0 Device Authorization Grant
- [RFC8707](https://datatracker.ietf.org/doc/html/rfc8707): Resource Indicators for OAuth 2.0
- [RFC9207](https://datatracker.ietf.org/doc/html/rfc9207): OAuth 2.0 Authorization Server Issuer Identification
- [RFC9449](https://datatracker.ietf.org/doc/html/rfc9449): OAuth 2.0 Demonstrating Proof of Possession (DPoP)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [Draft](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics): OAuth 2.0 Security Best Current
    Practice
- [Risk of phishing Access Tokens from clients using OIDC Authentication](https://docs.google.com/document/d/1TdcBtRu4yNXQkI7ZdKWZlSIaWs29tIQblyS3805nK1A/edit?tab=t.0)

# Appendix A: Multiple MongoClients

Some applications may require support for multiple concurrent MongoClients using the same OIDC tokens. In this case, a
token set (access token, ID token and refresh token) may be re-used, if and only if:

- The `username` parameter is equal
- The IdP metadata provided by the MongoDB endpoint is equal
- Both token sets contain an ID token and the respective `aud` and `sub` claims[^5] of the ID tokens are equal, OR
    neither token set contains an ID token

If an application supports multiple MongoClients, it MUST ensure that only one token acquisition flow is in use at the
same time, and coordinate token refresh intervals accordingly.

The Developer Tools team maintains an implementation that integrates with multiple MongoClient instances at
[https://github.com/mongodb-js/oidc-plugin](https://github.com/mongodb-js/oidc-plugin), which can be used as a reference
implementation (and which can generally be used in other applications based on the Node.js driver, although as a
standalone package it is not considered a supported product of MongoDB).

# Appendix B: Future intentions for endpoint restrictions

Currently, users who connect to a host other than localhost or an Atlas hostname need to specify this host in the
`ALLOWED_HOSTS` auth mechanism property. In the future, MongoDB is hoping to support Demonstrating Proof of Possession
(DPoP, [RFC9449](https://datatracker.ietf.org/doc/html/rfc9449)) which will allow lifting this restriction. The goal
here of either of these mechanisms is to prevent users from connecting to untrusted endpoints that could advertise
attacker-controlled IdP metadata and intercept tokens intended for other clusters (or even non-MongoDB OIDC
applications).

We would also like to adopt [RFC8707](https://datatracker.ietf.org/doc/html/rfc8707), but have not decided on a specific
format for expressing MongoDB clusters as resource URLs.

## Changelog

- 2024-11-14: Initial version.

[^1]: Technically, this refers to an Authorization Server (AS). Inside MongoDB, the usage of AS and IdP has been
    considered more or less interchangeable.

[^2]: At the time of writing, there are Identity Providers which do not support JWT access tokens, but which do provide
    JWT ID tokens that are usable for authentication. This requires opt-in on both the server configuration side and the
    client side.

[^3]: The `offline_access` scope is what provides the ability to refresh tokens without performing a full
    re-authentication. Some particularly security-sensitive customers may choose this approach at the expense of a
    greatly diminished UX, where users need to frequently re-authenticate.

[^4]: [RFC8252](https://datatracker.ietf.org/doc/html/rfc8252) lays out alternatives to this approach, such as registering
    a custom URI scheme handler or registering “Claims” on specific HTTPS URLs, but we’ve decided not to pursue these
    approaches in any existing applications, since some of our applications are CLI applications without an installation
    step where neither of these alternative approaches is feasible.

[^5]: OIDC as a protocol allows for `aud` claims that contain multiple strings, instead of a single one. MongoDB endpoints
    are [restricted](https://jira.mongodb.org/browse/SERVER-86607) to single-value `aud` claims, although client
    applications do not need to be concerned with this restriction.
