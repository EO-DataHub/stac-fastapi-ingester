# Changelog

## 0.1.7 (22-08-2024)
Added unit tests
- Code cleanup to support better unit testing
- Updated logging for https responses
- Updated handling of botocore ClientError exception


## v0.1.6 (30-07-2024)

Added support for access-control when creating, updating and deleting entries
- Added workspace parameter to requests calls to identify the current workspace from the Pulsar message to allow access to be confirmed by STAC-FastApi
- Added is_public parameter to create requests to specify whether the catalog or collection to be created should be available publicly in the catalogue or not 

## v0.1.5 (08-07-2024)

Bugfix
- Corrected update_catalog functionality to ensure full catalog path, including current catalog_id, is used in the request to update the catalog

## v0.1.4 (02-07-2024)

Efficiency Improvements
- Update code to sort input lists `added_keys` and `updated_keys` by path length (number of "/") to ensure higher-level catalogs and collections are ingested before their nested datasets (child catalogs, collections and items).

Code cleanup
- Update logging outputs to better identify catalog ids

## v0.1.3 (13-06-2024)
- Added support for arbitrarily nested catalogs
- Updated code correctly identify parent catalogs from the keys in the provided Pulsar message
- Updated endpoint logic to correctly pass catalog paths to STAC-Fastapi for ingesting
- Removed unnecessary function and variables for previous catalog identification method
- Minor updates to logging and error handling to improve robustness
- Corrected logging time to be UTC

## v0.1.2 (16-05-2024)
- Updated to support catalogues, updates to endpoints
- Updated logging for catalogues with more detailed warnings

## v0.1.1 (25-04-2024)
- Added workflows
- Updated error messages for debugging
- Updated AWS connection 
- No KeyError if files are invalid

## v0.1.0 (12-04-2024)

- Initial commit of STAC Fastapi ingester
  - Pulsar subscriber to listen to specific topic
  - Ingester triggered by pulsar to ingest S3 files into STAC Fastapi
  - Test script to allow manual publishing of messages to trigger ingest pipeline
  - Dockerfile to build module for deployment