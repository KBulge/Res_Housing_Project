import os
from datetime import datetime, timezone
from dotenv import load_dotenv
import pandas as pd

from snowflake.connector.pandas_tools import write_pandas
from src.snowflake.connection import get_connection
#from src.ingestion.parcllabs import ingest_parcllabs_data

load_dotenv()

def load_adjustments(df, source):

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.date
    
    df["load_timestamp"] = datetime.now(timezone.utc)
    df["source"] = source
    df.columns = df.columns.str.upper()

    return df

def load_dataframe(df, table_name):

    passcode = input("Enter Snowflake MFA code: ")

    conn = get_connection(passcode)

    success, nchunks, nrows, _ = write_pandas(
        conn=conn,
        df=df,
        table_name=table_name,
        database="RES_HOUSING",
        schema="BRONZE",
        overwrite=False
    )

    conn.close()

    return success, nrows

def main():
    #total_sf_stock, portfolio_sf_stock, sf_housing_event_counts = ingest_parcllabs_data()
    total_sf_stock = pd.read_csv("data/raw/total_stock_2025-01-01_2025-03-31.csv")

    total_sf_stock = load_adjustments(
        total_sf_stock,
        "parcl_sf_housing_stock"
    )

    portfolio_sf_stock = pd.read_csv("data/raw/portfolio_sf_stock_2025-01-01_2025-03-31.csv")

    portfolio_sf_stock = load_adjustments(
        portfolio_sf_stock,
        "parcl_sf_portfolio_stock"
    )

    sf_housing_event_counts = pd.read_csv("data/raw/sf_housing_event_counts_2025-01-01_2025-03-31.csv")

    sf_housing_event_counts = load_adjustments(
        sf_housing_event_counts,
        "parcl_sf_housing_events"
    )

    markets_df = pd.read_csv("data/raw/markets.csv")
    markets_df = markets_df[['parcl_id', 'name', 'location_type']]

    markets_df = load_adjustments(
        markets_df,
        "parcl_markets"
    )

    load_dataframe(
        markets_df,
        "RAW_MARKETS"
    )

    load_dataframe(
        total_sf_stock,
        "RAW_SF_HOUSING_STOCK"
    )

    load_dataframe(
        portfolio_sf_stock,
        "RAW_SF_PORTFOLIO_STOCK"
    )
    
    load_dataframe(
        sf_housing_event_counts,
        "RAW_SF_HOUSING_EVENTS"
    )

    print("Loaded data into Snowflake!")

if __name__ == "__main__":
    main()