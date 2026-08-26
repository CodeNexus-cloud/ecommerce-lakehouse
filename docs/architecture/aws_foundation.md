# AWS Foundation

## Purpose

Amazon S3 provides the cloud object storage layer for the
e-commerce lakehouse.

## Storage Layers

- Bronze - raw source extracts
- Silver - cleaned and standardized data
- Gold - analytics-ready dimensional data
- Rejected - records failing data quality rules
- Monitoring - pipeline and data-quality metadata

## Security

- S3 Block Public Access enabled
- S3 bucket versioning enabled
- Server-side encryption enabled
- Databricks will access S3 through IAM-based authentication
- Long-lived AWS credentials will not be stored in the repository

## Architecture

PostgreSQL
    |
    v
Databricks
    |
    v
Amazon S3
    |
    +-- Bronze
    +-- Silver
    +-- Gold
    +-- Rejected
    +-- Monitoring 