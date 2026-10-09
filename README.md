# Residential Housing Capital Exposure

Personal data engineering project analyzing U.S. residential housing markets and investor activity using Parcl Labs data.

## Project Overview

This project focuses on analyzing investor-owned residential housing stock and housing market activity across selected U.S. metropolitan areas. The eventual goal is to develop a **Capital Exposure Score** that helps quantify the concentration of large-scale investor activity within residential housing markets.

## Technology Stack

* Python
* SQL
* Snowflake
* Pandas
* Parcl Labs API
* Git / GitHub
* GitHub Actions

## Architecture

```text
Parcl Labs API
      ↓
Python Ingestion
      ↓
Snowflake Bronze Staging
      ↓
Snowflake Bronze MERGE
      ↓
Snowflake Silver Staging
      ↓
Silver Validation
      ↓
Snowflake Silver MERGE
      ↓
Snowflake Gold Staging
      ↓
Gold Validation
      ↓
Snowflake Gold MERGE
      ↓
Analytics
```

### Data Processing and Orchestration

The pipeline uses staging tables, validation, and MERGE operations to process data through the Bronze, Silver, and Gold layers.

* **Bronze:** Ingests source data into Snowflake and loads staging tables before updating production tables.
* **Silver:** Extracts data from upstream Bronze production tables using watermarks, loads staging tables, validates the data, and merges results into Silver production tables.
* **Gold:** Extracts data from upstream Silver production tables using watermarks, loads staging tables, validates the data, and merges results into Gold production tables.

### Watermark Management

The pipeline uses a centralized `CONTROL.WATERMARKS` table to track incremental processing by schema, production table, and date key.

Seven watermark records are planned:

* Three Bronze production tables.
* Three Silver production tables.
* One shared Gold watermark record, `GOLD.GOLD_DATE`, used to track processing across all three Gold datasets.

Watermark records are initialized with `NULL` values for the initial load. When a watermark is `NULL`, staging logic retrieves the full available upstream dataset. Once processing succeeds, the watermark is updated to reflect the latest successfully processed date.

Subsequent runs use the stored watermark to retrieve records on or after the last processed date.

### Transaction Handling

SQL execution is managed through the reusable `run_sql.py` module, which supports independent statement execution and transactional execution.

* **Bronze and Silver:** SQL statements execute independently, allowing successful statements to commit without requiring the entire SQL file to succeed.
* **Gold:** All statements in a Gold SQL file execute within a single transaction. Due to dimensional model tranformations, the transaction commits only after all MERGE and watermark update statements succeed. If a statement fails, Python attempts to roll back the transaction.

Gold transaction handling is enabled through the `transactional` command-line argument. Transaction control is managed in Python rather than embedded in the SQL files.

## Repository Structure

```text
Res_Housing_Project/
├── src/
├── config/
├── .gitignore
├── .github/workflows/
├── requirements.txt
└── README.md
```

## Current Status

In active development.

Core data ingestion, Snowflake dimensional modeling, validation, staging, watermark-based incremental processing, and CI/CD infrastructure are implemented or undergoing integration testing. The GitHub Actions pipeline is currently undergoing end-to-end testing and debugging.

## Future Goals

* Automate data ingestion and transformation.
* Finalize GitHub Actions CI/CD and pipeline orchestration.
* Expand market coverage.
* Develop the Capital Exposure Score.
* Add analytical reporting and visualization.
