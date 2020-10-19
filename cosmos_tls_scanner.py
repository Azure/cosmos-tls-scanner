# MIT License

# Copyright (c) Microsoft Corporation.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE

import argparse
import base64
import datetime
import hashlib
import hmac
import requests
import ssl
import urllib.parse

from urllib3.poolmanager import PoolManager


class SSLAdapter(requests.adapters.HTTPAdapter):
    """ An HTTPS Transport Adapter that uses an arbitrary SSL version. """

    def __init__(self, ssl_version=None, **kwargs):
        self.ssl_version = ssl_version
        super(SSLAdapter, self).__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_version=self.ssl_version,
        )


def _get_auth_header(key, verb, resource_type, resource_link, date):
    """
    Function to create Azure Cosmos DB auth hash signature
    More details here: https://docs.microsoft.com/en-us/rest/api/cosmos-db/access-control-on-cosmosdb-resources
    Args:
      key: Master key for Azure Cosmos DB.
      verb: REST call verb. Example "get", "post".
      resource_type: Resource being accessed. Example "dbs", "colls", "docs"
      resource_link: Portion of the string is the identity property of the resource that the request is
          directed at. Example "dbs/MyDatabase/colls/MyCollection"
      date: Current date in HTTP-date string format. Example "Tue, 01 Nov 1994 08:12:31 GMT"
    """
    payload = "{}\n{}\n{}\n{}\n\n".format(
        verb.lower(), resource_type.lower(), resource_link, date.lower()
    )
    digest = hmac.digest(base64.b64decode(key), payload.encode("utf-8"), hashlib.sha256)
    signature = base64.encodebytes(digest).decode("utf-8")
    return urllib.parse.quote("type=master&ver=1.0&sig={}".format(signature[:-1]))


def _send_request(
    uri, ssl_version, verb, resource_type, resource_link, headers=None, body=None
):
    """ Send REST call with given ssl_version """
    full_url = urllib.parse.urljoin(uri, resource_link + "/")
    full_url = urllib.parse.urljoin(full_url, resource_type)
    session = requests.Session()
    session.mount("https://", SSLAdapter(ssl_version))
    response = session.request(verb, full_url, headers=headers, data=body)
    return response


def list_databases(uri, key, ssl_version):
    """ Basic call to list all databases in an account """
    verb = "get"
    resource_type = "dbs"
    resource_link = ""
    date = datetime.datetime.utcnow()
    date_str = date.strftime("%a, %d %b %Y %H:%M:%S GMT").lower()

    headers = {
        "authorization": _get_auth_header(
            key, verb, resource_type, resource_link, date_str
        ),
        "x-ms-version": "2017-02-22",
        "x-ms-date": date_str,
        "x-ms-max-item-count": "1",
        "Cache-Control": "no-cache",
    }
    return _send_request(uri, ssl_version, verb, resource_type, resource_link, headers)


def basic_query(uri, key, ssl_version, database_name, container_name):
    """ Basic call to query one element from given database, container """
    verb = "post"
    resource_type = "docs"
    resource_link = "dbs/{}/colls/{}".format(database_name, container_name)
    date = datetime.datetime.utcnow()
    date_str = date.strftime("%a, %d %b %Y %H:%M:%S GMT").lower()

    headers = {
        "content-type": "application/query+json",
        "authorization": _get_auth_header(
            key, verb, resource_type, resource_link, date_str
        ),
        "x-ms-version": "2017-02-22",
        "x-ms-date": date_str,
        "x-ms-documentdb-isquery": "True",
        "Cache-Control": "no-cache",
    }

    body = '{"query":"SELECT 1"}'
    return _send_request(
        uri, ssl_version, verb, resource_type, resource_link, headers, body
    )


def _get_parser():
    """
    Gets argparse parser object
    Args:
      --endpoint: Database account endpoint. Example https://myaccount.documents.azure.com:443/
      --authorization-key: Master or Read-only key for account of the form khYANAIiAl12n...==
      --database-name: Name of the Azure Cosmos DB database in the account.
      --collection-name: Name of the collection in the database.
    """
    parser = argparse.ArgumentParser(description="Azure Cosmos DB TLS Scanner")
    parser.add_argument(
        "--endpoint",
        "-e",
        required=True,
        help="Azure Cosmos DB database account endpoint. Example https://myaccount.documents.azure.com:443/",
    )
    parser.add_argument(
        "--authorization-key",
        "-k",
        required=True,
        help="Master or Read-only key for account of the form khYANAIiAl12n...==",
    )
    parser.add_argument(
        "--database-name",
        "-d",
        default=None,
        help="Optional name of the database where to test TLS.",
    )
    parser.add_argument(
        "--collection-name",
        "-c",
        default=None,
        help="Optional name of the collection where to test TLS.",
    )
    return parser


def _get_supported_ssl_versions():
    """ Get list of all client supported SSL versions of form (SSL version name, ssl flag) """
    ssl_versions = []
    ssl_versions.append(
        (
            "SSL V2 (not supported by Azure Cosmos DB)",
            ssl.PROTOCOL_SSLv2 if ssl.HAS_SSLv2 else None,
        )
    )
    ssl_versions.append(
        (
            "SSL V3 (not supported by Azure Cosmos DB)",
            ssl.PROTOCOL_SSLv3 if ssl.HAS_SSLv3 else None,
        )
    )
    ssl_versions.append(("TLS V1  ", ssl.PROTOCOL_TLSv1 if ssl.HAS_TLSv1 else None))
    ssl_versions.append(("TLS V1.1", ssl.PROTOCOL_TLSv1_1 if ssl.HAS_TLSv1_1 else None))
    ssl_versions.append(("TLS V1.2", ssl.PROTOCOL_TLSv1_2 if ssl.HAS_TLSv1_2 else None))
    ssl_versions.append(
        (
            "TLS V1.3",
            ssl.OP_NO_SSLv2
            & ssl.OP_NO_SSLv3
            & ssl.OP_NO_TLSv1
            & ssl.OP_NO_TLSv1_1
            & ssl.OP_NO_TLSv1_2
            if ssl.HAS_TLSv1_2
            else None,
        )
    )
    return ssl_versions


def main(args):
    args.endpoint = args.endpoint.strip()
    args.authorization_key = args.authorization_key.strip()
    print("Endpoint: [{}]".format(args.endpoint))

    if args.database_name and args.collection_name:
        args.database_name = args.database_name.strip()
        args.collection_name = args.collection_name.strip()
        print(
            "Database name: [{}], Collection name: [{}]".format(
                args.database_name, args.collection_name
            )
        )

    ssl_versions = _get_supported_ssl_versions()

    print("\nSSL/TLS Version Support")

    for ssl_version_name, ssl_version in ssl_versions:
        if not ssl_version:
            print(ssl_version_name, ": Not supported by client")
        else:
            if args.database_name and args.collection_name:
                query_type = "Basic Query"
                response = basic_query(
                    args.endpoint,
                    args.authorization_key,
                    ssl_version,
                    args.database_name,
                    args.collection_name,
                )
            else:
                query_type = "List Databases"
                response = list_databases(
                    args.endpoint, args.authorization_key, ssl_version
                )

            if response.ok:
                print(ssl_version_name, query_type, ": Supported")
            elif "TLS" in response.text:
                print(ssl_version_name, query_type, ": Not supported")
            else:
                print("Connection error:", response.status_code, response.text)


if __name__ == "__main__":
    args_parser = _get_parser()
    args = args_parser.parse_args()
    main(args)
