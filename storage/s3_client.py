from dotenv import load_dotenv
import boto3
import os
from typing import Optional

# Load environment variables from .env file
load_dotenv()


def get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    """Return a secret from Streamlit or environment variables."""
    try:
        import streamlit as st
        from streamlit.errors import StreamlitSecretNotFoundError

        if hasattr(st, "secrets"):
            try:
                return st.secrets.get(name, os.getenv(name, default))
            except StreamlitSecretNotFoundError:
                return os.getenv(name, default)
    except ModuleNotFoundError:
        pass

    return os.getenv(name, default)


# S3Storage class for interacting with AWS S3
class S3Storage:

    def __init__(self):
        # Initialize the S3Storage class with AWS credentials and bucket name from environment variables or Streamlit secrets
        self.bucket_name = get_secret("AWS_BUCKET_NAME")

        self.client = boto3.client(
            "s3",
            aws_access_key_id=get_secret("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=get_secret("AWS_SECRET_ACCESS_KEY"),
            region_name=get_secret("AWS_REGION")
        )

    def upload_file(self, local_path: str, s3_key: str):
        # Upload a file to the S3 bucket
        self.client.upload_file(
            local_path,
            self.bucket_name,
            s3_key
        )

    def download_file(self, s3_key: str, local_path: str):
        # Download a file from the S3 bucket
        self.client.download_file(
            self.bucket_name,
            s3_key,
            local_path
        )

    def get_file_content(self, s3_key: str):
        # Get the content of a file from the S3 bucket
        response = self.client.get_object(
            Bucket=self.bucket_name,
            Key=s3_key
        )
        return response['Body'].read().decode('utf-8')

    def list_files(self, prefix: str):
        # List files in the S3 bucket with a specific prefix
        response = self.client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=prefix
        )

        return [
            obj["Key"]
            for obj in response.get("Contents", [])
        ]
    
    @staticmethod
    def article_key(date: str):
        return f"articles/{date}.json"

    @staticmethod
    def briefing_key(date: str):
        return f"briefings/IB_{date}.md"