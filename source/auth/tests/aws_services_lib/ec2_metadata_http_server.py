#! /usr/bin/env python3
"""Mock AWS EC2 Metadata Endpoint."""

import argparse
import collections
import base64
import http.server
import json
import logging
import socketserver
import sys
import urllib.parse
import ssl

import aws_common

fault_type = None

"""Fault which causes encrypt to return 500."""
FAULT_500 = "fault_500"

# List of supported fault types
SUPPORTED_FAULT_TYPES = [
    FAULT_500,
]

IMDS_API_TOKEN = "SECRET_API_TOKEN"
IMDS_METADATA_TOKEN_HEADER = "x-aws-ec2-metadata-token"

class AwsEC2MetadataHandler(http.server.BaseHTTPRequestHandler):
    """
    Handle requests from AWS EC2 Metadata Monitoring and test commands
    """

    def do_PUT(self):
        """Serve a Test PUT request."""
        parts = urllib.parse.urlsplit(self.path)
        path = parts[2]

        expect = self.headers.get("expect")
        if expect:
            self.send_response(http.HTTPStatus.EXPECTATION_FAILED)
            self.end_headers()
            self.wfile.write("Do not send the Expect header, AWS does not handle it".encode())
            return

        if path == "/latest/api/token":
            self._do_api_token()
        else:
            self.send_response(http.HTTPStatus.NOT_FOUND)
            self.end_headers()
            self.wfile.write("Unknown URL".encode())

    def do_GET(self):
        """Serve a Test GET request."""
        parts = urllib.parse.urlsplit(self.path)
        path = parts[2]

        api_token = self.headers.get(IMDS_METADATA_TOKEN_HEADER)
        print(f"API TOKEN: {api_token}")
        if api_token != IMDS_API_TOKEN:
            self.send_response(http.HTTPStatus.FORBIDDEN)
            self.end_headers()
            self.wfile.write("Missing API Token".encode())
            return

        if path == "/latest/meta-data/iam/security-credentials/":
            self._do_security_credentials()
        elif path == "/latest/meta-data/iam/security-credentials/mock_role":
            self._do_security_credentials_mock_role()
        else:
            self.send_response(http.HTTPStatus.NOT_FOUND)
            self.end_headers()
            self.wfile.write("Unknown URL".encode())


    def _send_reply(self, data, status=http.HTTPStatus.OK):
        print("Sending Response: " + data.decode())

        self.send_response(status)
        self.send_header("content-type", "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()

        self.wfile.write(data)


    def _send_header(self):
        self.send_response(http.HTTPStatus.OK)
        self.send_header("content-type", "application/octet-stream")
        self.end_headers()

    def _do_api_token(self):
        self._send_header()

        self.wfile.write(IMDS_API_TOKEN.encode('utf-8'))

    def _do_security_credentials(self):
        self._send_header()

        self.wfile.write(str("mock_role").encode('utf-8'))

    def _do_security_credentials_mock_role(self):
        if fault_type == FAULT_500:
            return self._do_security_credentials_mock_role_faults()

        self._send_header()

        str1 = f"""{{
  "Code" : "Success",
  "LastUpdated" : "2019-11-20T17:19:19Z",
  "Type" : "AWS-HMAC",
  "AccessKeyId" : "{aws_common.MOCK_AWS_TEMP_ACCOUNT_ID}",
  "SecretAccessKey" : "{aws_common.MOCK_AWS_TEMP_ACCOUNT_SECRET_KEY}",
  "Token" : "{aws_common.MOCK_AWS_TEMP_ACCOUNT_SESSION_TOKEN}",
  "Expiration" : "2019-11-20T23:37:45Z"
}}"""

        self.wfile.write(str1.encode('utf-8'))

    def _do_security_credentials_mock_role_faults(self):
        if fault_type == FAULT_500:
            self._send_reply("Fake Internal Error.".encode(), http.HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        raise ValueError("Unknown Fault Type: %s" % (fault_type))


def run(port, server_class=http.server.HTTPServer, handler_class=AwsEC2MetadataHandler):
    """Run web server."""
    server_address = ('', port)

    httpd = server_class(server_address, handler_class)

    print("Mock EC2 Instance Metadata Web Server Listening on %s" % (str(server_address)))

    httpd.serve_forever()


def main():
    """Main Method."""
    global fault_type
    global disable_faults

    parser = argparse.ArgumentParser(description='MongoDB Mock AWS EC2 Metadata Endpoint.')

    parser.add_argument('-p', '--port', type=int, default=8000, help="Port to listen on")

    parser.add_argument('-v', '--verbose', action='count', help="Enable verbose tracing")

    parser.add_argument('--fault', type=str, help="Type of fault to inject")

    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    if args.fault:
        if args.fault not in SUPPORTED_FAULT_TYPES:
            print("Unsupported fault type %s, supports types are %s" % (args.fault, SUPPORTED_FAULT_TYPES))
            sys.exit(1)

        fault_type = args.fault

    run(args.port)


if __name__ == '__main__':

    main()
