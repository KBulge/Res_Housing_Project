import os
from dotenv import load_dotenv

import pandas as pd
from parcllabs import ParclLabsClient


load_dotenv()
api_key = os.getenv("PARCLLABS_API_KEY")

client = ParclLabsClient(api_key)

def ingest_parcllabs_data():
    api_key = os.getenv("PARCLLABS_API_KEY")

    client = ParclLabsClient(api_key)

    start_date="2025-01-01"
    end_date="2025-03-31"

    market_df = pd.read_csv("config/markets.csv")

    market_parcl_ids = market_df["parcl_id"].tolist()

    total_sf_stock = client.market_metrics.housing_stock.retrieve(
        parcl_ids=market_parcl_ids,
        start_date=start_date,
        end_date=end_date,
    )

    portfolio_sf_stock = client.portfolio_metrics.sf_housing_stock_ownership.retrieve(
        parcl_ids=market_parcl_ids,
        start_date=start_date,
        end_date=end_date,
    )

    port_sizes = ["2_TO_9", "10_TO_99", "100_TO_999", "1000_PLUS"]

    sf_housing_event_counts = pd.DataFrame()

    for port_range in port_sizes:
        results = client.portfolio_metrics.sf_housing_event_counts.retrieve(
            parcl_ids=market_parcl_ids,
            start_date=start_date,
            end_date=end_date,
            portfolio_size=f"PORTFOLIO_{port_range}"
        )

        sf_housing_event_counts = pd.concat([sf_housing_event_counts, results], ignore_index=True)

    print("Successfully Ingested data!")

    return total_sf_stock, portfolio_sf_stock, sf_housing_event_counts