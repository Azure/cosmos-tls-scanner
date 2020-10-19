# Cosmos TLS Scanner

This utility can be used to detect the supported TLS version for a given Azure Cosmos DB account.

Note that this utility would only be able to test the account against TLS versions supported by the client system running the script.

Supported TLS version:
- SSL V2
- SSL V3
- TLS V1
- TLS V1.1
- TLS V1.2
- TLS V1.3

## Getting started

### Prerequisites
- [Python 3.5.3+][python]
- Install requirements from requirements.txt
- A Azure Cosmos DB SQL API account to test for supported TLS versions.
    - Account endpoint like https://myaccount.documents.azure.com:443/
    - Any of the read-write or read-only [primary keys][primary_keys]
    - Optional database and collection name.

### Running the TLS scanner util

Installing requirements.txt
```bash
pip install -r requirements.txt
```

Run the utility with a given Azure Cosmos DB endpoint as follows
```bash
python3 cosmos_tls_scanner.py --endpoint https://myaccount.documents.azure.com:443/ --authorization-key khYANAIiAl12n...==
```
Or additionally provide the database and collection name to test the TLS version against
```bash
python3 cosmos_tls_scanner.py --endpoint https://myaccount.documents.azure.com:443/ --authorization-key khYANAIiAl12n...== --database-name MyDatabase --collection-name MyCollection
```

### Interpreting results

On running the script, we see results that look like this
```
Endpoint: [https://myaccount.documents.azure.com:443/]
Database name: [MyDatabase], Collection name: [MyCollection]

SSL/TLS Version Support
SSL V2 (not supported by Azure Cosmos DB) : Not supported by client
SSL V3 (not supported by Azure Cosmos DB) : Not supported by client
TLS V1   Basic Query : Not supported
TLS V1.1 Basic Query : Supported
TLS V1.2 Basic Query : Supported
TLS V1.3 : Not supported by client
```

This result indicates that TLS V1 is not accepted by Azure Cosmos DB while TLS V1.1 and TLS V1.2 are. We can not verify TLS V1.3 support as it is not supported from the client side. This can also happen if python isn't compiled with the latest version of openssl. By default, Azure Cosmos DB doesn't support SSL V2 and SSL V3.

Here `Basic Query` means that we are querying from the given database and collection for one element to verify the connection. If the database and collection name is not supplied, we verify the TLS version by listing databases for the account, shown as `List Databases`.

## Support

This project uses [GitHub Issues][github_issues] to track bugs and feature requests. Please search the existing issues before filing new issues to avoid duplicates. For new issues, file your bug or feature request as a new Issue.

## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft 
trademarks or logos is subject to and must follow 
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.

<!-- Links -->
[python]: https://www.python.org/downloads/
[primary_keys]: https://docs.microsoft.com/en-us/azure/cosmos-db/secure-access-to-data#primary-keys
[github_issues]: https://github.com/Azure/cosmos-tls-scanner/issues