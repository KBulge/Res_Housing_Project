import argparse
from yaml import safe_load
import pandas as pd

import snowflake.connector as sc
from snowflake.connector.pandas_tools import write_pandas
from src.snowflake.connection import get_connection

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

def get_watermark(schema_name, table_name, date_key, conn=None):
    """
    Reads the last watermark for each prod table
    Assumes connection is already established
    """
    query = f"""
        SELECT LAST_WATERMARK
        FROM RES_HOUSING.CONTROL.WATERMARKS
        WHERE SCHEMA_NAME = '{schema_name}'
        AND TABLE_NAME = '{table_name}'
        AND DATE_KEY = '{date_key}'
        ORDER BY LAST_WATERMARK DESC
        LIMIT 1;
    """

    try:
        cursor = conn.cursor()

        cursor.execute(query)
        result = cursor.fetchone()
    except sc.errors.ProgrammingError as e:
        print(f"Error in fetching watermark: {e}")
        raise

    watermark = result[0] if result else None
    
    return watermark


def load_staging(layer_name):
    """
    1. Extract the latest watermark of each downstream prod table using get_watermarks()
    2. Query latest data in upstream prod table using the watermark as a filter - WHERE downstream_date >= upstream_date
    3. Load the data of the staging window into the staging tables
    """
    config = load_config(layer_name)

    with get_connection() as conn:

        if conn == None:
            print("Snowflake connection not set")
            raise

        for table in config.values():
            print("Processing table: ", table["staging"]["table"])

            watermark = get_watermark(
                table["downstream"]["schema"],
                table["downstream"]["table"],
                table["date_column"],
                conn
            )

            if watermark is None:
                query = f"""
                    SELECT *
                    FROM RES_HOUSING.{table["upstream"]["schema"]}.{table["upstream"]["table"]}
                """
            else:
                query = f"""
                    SELECT *
                    FROM RES_HOUSING.{table["upstream"]["schema"]}.{table["upstream"]["table"]}
                    WHERE DATE >= '{watermark}'
                """

            try:
                cursor = conn.cursor()

                staging_data = cursor.execute(query)
            except sc.errors.ProgrammingError as e:
                print(f"Error in fetching staging data: {e}")
                raise

            staging_data = pd.DataFrame(staging_data.fetchall(), columns=[col[0] for col in cursor.description])
            
            try:
                success, nchunks, nrows, _ = write_pandas(
                    conn=conn,
                    df=staging_data,
                    table_name=table["staging"]["table"],
                    database="RES_HOUSING",
                    schema=table["staging"]["schema"],
                    overwrite=True,
                    use_logical_type = True
                )

                print("Successfully written staging data:\n")
                print(f"Success: {success}, Chunks: {nchunks}, Rows: {nrows}")
            except sc.errors.ProgrammingError as e:
                print(f"Error in writing staging data: {e}")
                raise

            

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--layer",
        required=True,
        choices=["silver", "gold"],
        help="Layer to process"
    )

    args = parser.parse_args()

    load_staging(args.layer)