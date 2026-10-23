# Residential Housing Capital Exposure

A personal data engineering project analyzing U.S. residential housing markets and investor activity using Parcl Labs data.

## Project Overview

This project analyzes investor-owned residential housing stock and housing market activity across selected U.S. metropolitan areas. The eventual goal is to develop a **Capital Exposure Score** that helps quantify the concentration of large-scale investor activity within residential housing markets.

The project demonstrates data engineering best practices through API ingestion, incremental processing, dimensional modeling, data validation, and automated orchestration using Snowflake and GitHub Actions.

## Technology Stack

- Python
- SQL
- Snowflake
- Pandas
- Parcl Labs API
- Git / GitHub
- GitHub Actions

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

## Data Processing and Orchestration

The pipeline uses configuration-driven staging, data validation, MERGE operations, and watermark management to process data through the Bronze, Silver, and Gold layers.

### Bronze

- Retrieves source data from the Parcl Labs API using Python.
- Uses individual table watermarks to determine the ingestion date range.
- Loads API responses into Bronze staging tables.
- Merges staged data into Bronze production tables and updates the corresponding watermarks.

### Silver

- Retrieves upstream data from Bronze production tables using watermark-based date ranges.
- Overwrites Silver staging tables with the retrieved data.
- Validates staged data before merging it into Silver production tables.
- Updates watermarks following successful processing.

### Gold

- Retrieves upstream data from Silver production tables using watermark-based date ranges.
- Overwrites Gold staging tables with the retrieved data.
- Validates staged data before merging it into Gold production tables.
- Processes Gold MERGE and watermark updates within a single transaction to maintain consistency.

### Orchestration

The `load_staging.py` module serves as the central entry point for staging operations across all three layers.

Layer-specific behavior is driven by `staging_config.yaml`, keeping table configurations separate from the orchestration logic.

Bronze ingestion uses `parcl_ingestion.py` to handle the Parcl Labs API requests, while `load_staging.py` coordinates date ranges and staging writes.

Example execution commands:

```bash
python -m src.snowflake.load_staging --layer bronze
python -m src.snowflake.load_staging --layer silver
python -m src.snowflake.load_staging --layer gold
```

## Watermark Management

The pipeline uses a centralized `RES_HOUSING.CONTROL.WATERMARKS` table to track incremental processing by schema, production table, and date key.

The watermark configuration covers seven records:

- Three Bronze production tables.
- Three Silver production tables.
- One shared Gold watermark record, `GOLD.GOLD_DATE`, used to track processing across the Gold datasets.

Watermarks are retrieved in a single query per layer and stored in a dictionary for use during table processing.

For Bronze ingestion, each table uses its own watermark to determine the API request's start date. Tables without an existing watermark use January 1, 2025, as the initial start date. The end date is set to the current date.

For Silver and Gold, the orchestration retrieves upstream data using the applicable watermark date. Processing includes the watermark date to support reprocessing of overlapping data.

Staging tables are overwritten during each run, while production tables are updated through MERGE operations. This allows records to be reprocessed without unnecessarily duplicating existing production data, assuming the relevant MERGE keys correctly identify each record.

## Transaction Handling

SQL execution is managed through the reusable `run_sql.py` module.

- **Bronze and Silver:** SQL statements execute independently. The orchestration stops on processing errors to prevent subsequent production operations from proceeding after a failed staging or validation step.
- **Gold:** MERGE and watermark update statements execute within a single transaction. The transaction commits only after all statements succeed. If a statement fails, Python attempts to roll back the transaction.

Gold transaction handling is enabled through the `transactional` command-line argument. Transaction control is managed in Python rather than embedded in the SQL files.

## Repository Structure

```text
Res_Housing_Project/
├── src/
│   ├── snowflake/
│   │   ├── load_staging.py
│   │   ├── run_sql.py
│   │   └── ...
│   └── ...
├── config/
│   └── staging_config.yaml
├── .github/
│   └── workflows/
├── .gitignore
├── requirements.txt
└── README.md
```

## Current Status

The core data ingestion and transformation pipeline has been implemented and successfully executed in the local development environment against Parcl Labs and Snowflake.

Local testing has verified data from **January 1, 2025, through September 1, 2026**, with the following record counts:

| Dataset | Records per layer |
|---|---:|
| Housing stock | 105 |
| Housing events | 420 |

The counts were verified across the corresponding Bronze, Silver, and Gold datasets.

The implementation includes:

- Parcl Labs API ingestion.
- Configuration-driven staging operations.
- Bronze, Silver, and Gold dimensional modeling.
- Watermark-based incremental processing.
- Data validation and MERGE operations.
- Transactional processing for Gold.
- GitHub Actions orchestration, pending further end-to-end verification following the latest changes.

## Future Goals

The next phase will focus on developing the analytical capabilities of the project.

- **Develop the Capital Exposure Score:** Design a reproducible metric for quantifying large-scale investor concentration in residential housing markets.
- **Expand analytical queries:** Examine investor ownership trends, portfolio-size distributions, and changes in investor activity over time.
- **Compare metropolitan markets:** Analyze differences in investor concentration and activity across selected U.S. housing markets.
- **Develop interactive visualizations:** Build a Snowflake Streamlit application to present findings and allow users to explore the data.
- **Document analytical methodology:** Explain metric definitions, assumptions, limitations, and findings to make the analysis transparent and reproducible.