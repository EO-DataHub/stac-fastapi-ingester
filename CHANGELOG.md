# Changelog

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
