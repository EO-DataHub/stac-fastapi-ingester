# Changelog

## v0.1.0 (12-04-2024)

- Initial commit of STAC Fastapi ingester
  - Pulsar subscriber to listen to specific topic
  - Ingester triggered by pulsar to ingest S3 files into STAC Fastapi
  - Test script to allow manual publishing of messages to trigger ingest pipeline
  - Dockerfile to build module for deployment
