# Changelog

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
