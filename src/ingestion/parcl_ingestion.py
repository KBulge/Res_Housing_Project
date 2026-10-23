import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

import pandas as pd
from parcllabs import ParclLabsClient

load_dotenv()

api_key = os.getenv("PARCLLABS_API_KEY")

client = ParclLabsClient(api_key)

def bronze_adjustments(df, source):

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.date
    
    df["load_timestamp"] = datetime.now(timezone.utc)
    df["source"] = source
    df.columns = df.columns.str.upper()

    return df

def ingest_parcllabs_data( table_name: str, start_date: str, end_date: str):
    """
    Function will be called for each table in the bronze layer
    Future To Do: Replace markets.csv with check on whether market parcl_ids have changed
        -Leaving as is for now to save on API costs
    """

    markets_df = pd.read_csv("config/markets.csv")

    market_parcl_ids = markets_df["parcl_id"].tolist()

    """
    #Future ingestion of markets to go here
    #Make sure to include in staging_config.yaml and load_staging.py
    ...

    markets_df = markets_df[['parcl_id', 'name', 'location_type']]
    markets_df = bronze_adjustments(
        markets_df,
        "parcl_markets"
    )
    """

    try:
        if table_name == "housing_stock":
            total_sf_stock = client.market_metrics.housing_stock.retrieve(
                parcl_ids=market_parcl_ids,
                start_date=start_date,
                end_date=end_date,
            )

            table_data = bronze_adjustments(
                total_sf_stock,
                "parcl_sf_housing_stock"
            )

        elif table_name == "portfolio_stock":
            portfolio_sf_stock = client.portfolio_metrics.sf_housing_stock_ownership.retrieve(
                parcl_ids=market_parcl_ids,
                start_date=start_date,
                end_date=end_date,
            )

            table_data = bronze_adjustments(
                portfolio_sf_stock,
                "parcl_sf_portfolio_stock"
            )

        elif table_name == "housing_events":
            port_sizes = ["2_TO_9", "10_TO_99", "100_TO_999", "1000_PLUS"]

            appended_sf_housing_events = pd.DataFrame()

            for port_range in port_sizes:
                results = client.portfolio_metrics.sf_housing_event_counts.retrieve(
                    parcl_ids=market_parcl_ids,
                    start_date=start_date,
                    end_date=end_date,
                    portfolio_size=f"PORTFOLIO_{port_range}"
                )

                appended_sf_housing_events = pd.concat([appended_sf_housing_events, results], ignore_index=True)

            table_data = bronze_adjustments(
                appended_sf_housing_events,
                "parcl_sf_housing_events"
            )

        else:
            raise ValueError(f"Invalid table name: {table_name}. Must be one of 'total_sf_stock', 'portfolio_sf_stock', or 'sf_housing_event_counts'.")

    except requests.exceptions.RequestException as e:
        print(f"Error in API request for table {table_name}: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error in ingesting data for table {table_name}: {e}")
        raise
    
    print("Successfully Ingested data from parcllabs!")

    return table_data