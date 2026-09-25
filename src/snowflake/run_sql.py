import sys
from pathlib import Path

from dotenv import load_dotenv

from src.snowflake.connection import get_connection


def run_sql(sql_file: str) -> None:
    conn = None

    try:
        load_dotenv()

        sql_path = Path(sql_file)

        if not sql_path.exists():
            raise FileNotFoundError(
                f"SQL file not found: {sql_path}"
            )

        sql = sql_path.read_text(encoding="utf-8")

        conn = get_connection()

        # Execute multiple SQL statements in the file.
        for statement in sql.split(";"):
            statement = statement.strip()

            if statement:
                conn.cursor().execute(statement)

        print(f"Successfully executed: {sql_path}")

    except Exception as exc:
        print(f"SQL execution failed: {type(exc).__name__}: {exc}")
        sys.exit(1)

    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_sql.py <sql_file>")
        sys.exit(1)

    run_sql(sys.argv[1])