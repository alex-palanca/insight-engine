import boto3
from config import env_ini as env
import json


# S3Storage class for interacting with AWS S3
class S3Storage:

    def __init__(self):
        # Initialize the S3Storage class with AWS credentials and bucket name from environment variables or Streamlit secrets
        self.bucket_name = env.get_env_var("AWS_BUCKET_NAME")

        self.client = boto3.client(
            "s3",
            aws_access_key_id=env.get_env_var("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=env.get_env_var("AWS_SECRET_ACCESS_KEY"),
            region_name=env.get_env_var("AWS_REGION")
        )

    def upload_content(self, content, s3_key: str):
        """Upload content to S3. Serializes non-string content to JSON.

        Args:
            content: Body of the file — str/bytes uploaded as-is, anything else
                    (list/dict) serialized to JSON text.
            s3_key: The S3 key (destination path).
        """
        if isinstance(content, str):
            body = content.encode("utf-8")
        elif isinstance(content, bytes):
            body = content
        else:
            body = json.dumps(content, ensure_ascii=False, default=str).encode("utf-8")

        self.client.put_object(Bucket=self.bucket_name, Key=s3_key, Body=body)

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

    @staticmethod
    def markdown_key(date: str):
        return f"markdown/{date}.md"

    @staticmethod
    def id_to_url_key(date: str):
        return f"id_to_url/{date}.json"