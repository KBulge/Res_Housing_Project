import sys
from pathlib import Path

from dotenv import load_dotenv

from src.snowflake.connection import get_connection


def run_sql(sql_file: str, transactional: bool = False) -> None:
    conn = None
    transaction_started = False

    try:
        load_dotenv()

        sql_path = Path(sql_file)

        if not sql_path.exists():
            raise FileNotFoundError(
                f"SQL file not found: {sql_path}"
            )

        sql = sql_path.read_text(encoding="utf-8")

        conn = get_connection()

        # Ensure independent statements commit individually
        # in Bronze and Silver.
        if not transactional:
            conn.autocommit(True)

        with conn.cursor() as cursor:

            # Begin one transaction when requested.
            if transactional:
                cursor.execute("BEGIN TRANSACTION")
                transaction_started = True

            # Execute multiple SQL statements in the file.
            for statement in sql.split(";"):
                statement = statement.strip()

                if statement:
                    cursor.execute(statement)

            # Commit only after every statement succeeds.
            if transactional:
                cursor.execute("COMMIT")
                transaction_started = False

        print(f"Successfully executed: {sql_path}")

    except Exception as exc:
        # Undo all changes made within the Gold transaction.
        if conn is not None and transaction_started:
            try:
                conn.rollback()
            except Exception as rollback_exc:
                print(
                    f"Rollback failed: "
                    f"{type(rollback_exc).__name__}: {rollback_exc}"
                )

        print(f"SQL execution failed: {type(exc).__name__}: {exc}")
        sys.exit(1)

    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        print("Usage: python run_sql.py <sql_file> [transactional]")
        sys.exit(1)

    sql_file = sys.argv[1]
    transactional = (
        len(sys.argv) == 3 and sys.argv[2].lower() == "true"
    )

    run_sql(sql_file, transactional=transactional)