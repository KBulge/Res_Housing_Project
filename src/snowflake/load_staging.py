import os
import sys
import argparse
from datetime import datetime
from yaml import safe_load
import pandas as pd
from dotenv import load_dotenv

import snowflake.connector as sc
from src.snowflake.connection import get_connection
from src.ingestion.parcl_ingestion import ingest_parcllabs_data
from snowflake.connector.pandas_tools import write_pandas

load_dotenv()

DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

def load_config(layer_name):
    """
    Opens the staging_config.yaml file and returns the configuration for the specified layer
    """
    try:
        with open("config/staging_config.yaml", "r") as file:
                # Use safe_load to parse the YAML data into a Python dict
                config = safe_load(file)
    except FileNotFoundError:
        print("The required configuration file is missing.")
        raise

    # Accessing the configuration values
    layer_dict = config[layer_name]

    return layer_dict

def get_watermarks(schema_name, conn=None):
    """
    Reads the last watermark for each prod table
    Assumes connection is already established
    Extracts ALL watermarks of a schema layer in one single query for reuse
    """
    query = f"""
        SELECT TABLE_NAME, LAST_WATERMARK
        FROM RES_HOUSING.CONTROL.WATERMARKS
        WHERE SCHEMA_NAME = '{schema_name}'
        QUALIFY ROW_NUMBER() OVER (PARTITION BY TABLE_NAME ORDER BY LAST_WATERMARK DESC) = 1;
    """

    try:
        cursor = conn.cursor()

        cursor.execute(query)
        results = cursor.fetch_pandas_all()

        if results.empty:
            print(f"No watermarks found for schema: {schema_name}")
            sys.exit(1)

        watermarks_dict = results.set_index('TABLE_NAME')['LAST_WATERMARK'].to_dict()
    except sc.errors.ProgrammingError as e:
        print(f"SQL error in fetching watermark: {e}")
        raise
    except sc.errors.OperationalError as e:
        print(f"Operational error in fetching watermark: {e}")
        raise
    except sc.errors.InterfaceError as e:
        print(f"Interface error in fetching watermark: {e}")
        raise

    return watermarks_dict


def load_staging(layer_name):
    """
    -Extract the latest watermark of each downstream prod table using get_watermarks()
    -Bronze: Retrieve data from ParclLabs from Bronze watermark date up to present day
        Note: Can potentially adjust to have end_date set manually as an arg in GH Action like 'dry_run'
    -Silver & Gold: Query latest data in upstream prod table using the watermark as a filter - WHERE downstream_date >= upstream_date
    -Load the data of the staging window into the staging tables
    """
    config = load_config(layer_name)

    with get_connection() as conn:

        if conn == None:
            print("Snowflake connection not set")
            raise

        #Watermarks extraction and conversion to dictionary to be reused in table loop below
        print("Extracting watermarks for layer: ", layer_name)
        watermarks = get_watermarks(
            layer_name.upper(),
            conn
        )

        #Verification of watermarks being extracted and converted to dict correctly
        print(watermarks)

        #Loops through tables in each layer to set the staging window data and write to staging tables in Snowflake 
        for table_name, table_data in config.items():
            print("Processing table: ", table_data["staging"]["table"])

            #Start of staging data extraction
            if layer_name == "bronze":
                #Extracts latest watermark for table key and converts to proper string format needed for parcllabs API calls
                watermark_key = f"raw_sf_{table_name}".upper()
                raw_date = watermarks.get(watermark_key)
                print(f"Watermark for {watermark_key}: {raw_date}")

                #Defaults to historical start date we've set for the pipeline data, thus determining new table behavior
                start_watermark = f"{raw_date:%Y-%m-%d}" if raw_date else "2025-01-01"

                table_start_date = start_watermark # Set to present day
                table_end_date = datetime.today().strftime('%Y-%m-%d')  # Convert to proper string format

                print("Start Date: ", table_start_date)
                print("End Date: ", table_end_date)

                #Will pass in table_name, start_date (bronze prod table watermark), end_date (present day) as args
                print("Calling ingest_parcllabs_data() for table: ", table_data["staging"]["table"])
                staging_data = ingest_parcllabs_data(
                    table_name=table_name,
                    start_date=table_start_date,
                    end_date=table_end_date
                )

            if layer_name == "silver" or layer_name == "gold":
                if layer_name == "silver":
                    watermark_key = f"sf_{table_name}".upper()
                    watermark = watermarks.get(watermark_key)
                    print(f"Watermark for {watermark_key}: {watermark}")

                if layer_name == "gold":
                    watermark_key = "GOLD_DATE"
                    watermark = watermarks.get(watermark_key)
                    print(f"Watermark for {watermark_key}: {watermark}")

                if watermark is None:
                    query = f"""
                        SELECT *
                        FROM RES_HOUSING.{table_data["upstream"]["schema"]}.{table_data["upstream"]["table"]}
                    """
                else:
                    query = f"""
                        SELECT *
                        FROM RES_HOUSING.{table_data["upstream"]["schema"]}.{table_data["upstream"]["table"]}
                        WHERE DATE >= '{watermark}'
                    """

                try:
                    cursor = conn.cursor()

                    staging_data = cursor.execute(query)
                except sc.errors.ProgrammingError as e:
                    print(f"Error in fetching staging data: {e}")
                    raise
                except sc.errors.OperationalError as e:
                    print(f"Operational error in fetching staging data: {e}")
                    raise
                except sc.errors.InterfaceError as e:
                    print(f"Interface error in fetching staging data: {e}")
                    raise

                staging_data = pd.DataFrame(staging_data.fetchall(), columns=[col[0] for col in cursor.description])

            print(f"Staging data for {table_data['staging']['table']} fetched successfully. Number of rows: {len(staging_data)}")

            #Simple stop on the run to test API ingestion ONLY
            if DRY_RUN == False:
                #Writes the staging data to the Snowflake staging table
                try:
                    success, nchunks, nrows, _ = write_pandas(
                        conn=conn,
                        df=staging_data,
                        table_name=table_data["staging"]["table"],
                        database="RES_HOUSING",
                        schema=table_data["staging"]["schema"],
                        overwrite=True,
                        use_logical_type = True
                    )

                    print("Successfully written staging data:\n")
                    print(f"Success: {success}, Chunks: {nchunks}, Rows: {nrows}")
                except sc.errors.ProgrammingError as e:
                    print(f"Error in writing staging data: {e}")
                    raise
                except sc.errors.OperationalError as e:
                    print(f"Operational error in fetching staging data: {e}")
                    raise
                except sc.errors.InterfaceError as e:
                    print(f"Interface error in fetching staging data: {e}")
                    raise
            if DRY_RUN == True:
                print(f"DRY RUN: Parcl ingestion successful for {table_name}.")
                print("DRY RUN: No data written to Snowflake.")

        print(f"load_staging.py for {layer_name} ran successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--layer",
        required=True,
        choices=["bronze", "silver", "gold"],
        help="Layer to process"
    )

    args = parser.parse_args()

    load_staging(args.layer)