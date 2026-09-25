import os

from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
import snowflake.connector


def get_connection():
    load_dotenv()

    private_key_passphrase = os.getenv(
        "SNOWFLAKE_PRIVATE_KEY_PASSPHRASE"
    )

    # Local development: read private key from file
    private_key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH")

    # GitHub Actions: read private key directly from environment variable
    private_key_contents = os.getenv("SNOWFLAKE_PRIVATE_KEY")

    if private_key_contents:
        private_key_data = private_key_contents.encode()
    elif private_key_path:
        with open(private_key_path, "rb") as key_file:
            private_key_data = key_file.read()
    else:
        raise ValueError(
            "No Snowflake private key found. "
            "Set SNOWFLAKE_PRIVATE_KEY or SNOWFLAKE_PRIVATE_KEY_PATH."
        )

    private_key = serialization.load_pem_private_key(
        private_key_data,
        password=private_key_passphrase.encode(),
    )

    private_key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        private_key=private_key_bytes,
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
    )