import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from src.snowflake.connection import get_connection


SQL_FILE = Path(__file__).with_name("validate_silver.sql")


def run_validation() -> None:
    """Run Silver data-quality checks and fail the pipeline when necessary."""

    conn = None

    try:
        load_dotenv()

        # Read validation SQL
        if not SQL_FILE.exists():
            raise FileNotFoundError(
                f"Validation SQL file not found: {SQL_FILE}"
            )

        sql = SQL_FILE.read_text(encoding="utf-8")

        # Connect to Snowflake
        print("Connecting to Snowflake...")
        conn = get_connection()

        # Execute validation SQL
        print("Running Silver validation checks...")
        results = pd.read_sql(sql, conn)

        if results.empty:
            raise RuntimeError(
                "Silver validation query returned no results."
            )

        # Make sure the expected columns exist
        required_columns = {"CHECK_NAME", "STATUS"}

        missing_columns = required_columns - set(results.columns)

        if missing_columns:
            raise RuntimeError(
                f"Validation results are missing required columns: "
                f"{', '.join(sorted(missing_columns))}"
            )

        # Display all validation results
        print("\nSilver Validation Results")
        print("=" * 60)
        print(results.to_string(index=False))

        # Identify failed checks
        failed_checks = results[
            results["STATUS"].astype(str).str.upper() != "PASS"
        ]

        if not failed_checks.empty:
            print("\nSILVER VALIDATION FAILED")
            print("=" * 60)

            for _, row in failed_checks.iterrows():
                print(f"- {row['CHECK_NAME']}: {row['STATUS']}")

            print("\nPipeline execution stopped.")
            sys.exit(1)

        # All checks passed
        print("\nSILVER VALIDATION PASSED")
        print("=" * 60)
        print("All Silver data-quality checks passed.")

        sys.exit(0)

    except Exception as exc:
        print("\nSILVER VALIDATION EXECUTION ERROR")
        print("=" * 60)
        print(f"{type(exc).__name__}: {exc}")
        print("\nPipeline execution stopped.")

        sys.exit(1)

    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    run_validation()