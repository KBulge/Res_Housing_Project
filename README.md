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
Snowflake Bronze
      ↓
Silver Validation / Quarantine
      ↓
Snowflake Silver
      ↓
Gold Validation
      ↓
Snowflake Gold
      ↓
Analytics
```

## Repository Structure

```text
Res_Housing_Project/
├── data/
├── notebooks/
├── src/
├── tests/
├── .gitignore
├── requirements.txt
└── README.md
```

## Current Status

Initial project architecture and Snowflake Bronze, Silver, and Gold layers are being developed.

## Future Goals

* Automate data ingestion and transformation
* Implement GitHub Actions CI/CD and pipeline orchestration
* Expand market coverage
* Develop the Capital Exposure Score
* Add analytical reporting and visualization
