"""S3 API wrappper handling S3 bucket operations"""

import typing
from io import BytesIO
from typing import Any

from botocore.exceptions import ClientError

from src.infrastructure.aws.aws_helper import AWSSessionManager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class S3Client:
    """AWS SDK S3 client for handling S3 bucket operations"""

    def __init__(self, session_manager: AWSSessionManager) -> None:
        self.session_manager = session_manager

    async def get_bucket_list(self) -> Any:
        """
        Gets the list of existing buckets in Amazon S3.

        :return: List of buckets or None if an error occurs
        """
        try:
            async with self.session_manager.session.client("s3", region_name=self.session_manager.region) as client:
                buckets = await client.list_buckets()
                logger.info(f"Retrieved bucket list: {buckets}")
                return buckets
        except ClientError as e:
            logger.error(f"Error encountered during retrieving list of buckets: {e}")
            raise

    async def check_if_bucket_exists(self, bucket_name: str) -> bool:
        """
        Checks if S3 bucket already exists.

        :bucket_name: Name of the S3 bucket to be checked
        :return: True if bucket exists, else False
        """
        bucket_list = await self.get_bucket_list()
        if bucket_list is None or "Buckets" not in bucket_list:
            return False
        for bucket in bucket_list["Buckets"]:
            if bucket_name == bucket["Name"]:
                return True
        return False

    async def create_bucket(self, bucket_name: str) -> bool:
        """
        Create an S3 bucket in a specified region
        If a region is not specified, the bucket is created in the S3 default
        region (eu-central-1).

        :bucket_name: Name of the S3 bucket to be created
        :return: True if bucket was created or already exists, else False
        """
        try:
            if await self.check_if_bucket_exists(bucket_name):
                return True
            async with self.session_manager.session.client("s3") as client:
                if self.session_manager.region is None or self.session_manager.region == "us-east-1":
                    await client.create_bucket(Bucket=bucket_name)
                else:
                    location_config = {"LocationConstraint": self.session_manager.region}
                    await client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=location_config)
                logger.info(f"Bucket {bucket_name} created successfully in {self.session_manager.region}.")
            return True
        except ClientError as e:
            logger.error(f"Error encountered during bucket creation: {e}")
            return False
        except Exception as e:
            logger.error(f"General error during bucket creation: {e}")
            return False

    async def delete_bucket(self, bucket_name: str) -> bool:
        """Deletes the S3 bucket"""
        try:
            logger.info(f"Deleting the S3 bucket {bucket_name}")
            async with self.session_manager.session.client("s3", region_name=self.session_manager.region) as client:
                response = await client.delete_bucket(Bucket=bucket_name)
            logger.info(f"Response: {response}")
            return True
        except ClientError as e:
            logger.error(f"Error encountered during deleting a bucket: {e}")
            raise RuntimeError(f"Deleting S3 bucket {bucket_name} not successful") from e

    async def delete_object_in_bucket(self, bucket_name: str, key: str) -> dict[str, Any]:
        """Deletes an object from the S3 bucket"""
        try:
            logger.info(f"Deleting object from S3 bucket {bucket_name} using key: {key}")
            async with self.session_manager.session.client("s3", region_name=self.session_manager.region) as client:
                response = await client.delete_object(
                    Bucket=bucket_name,
                    Key=key,
                )
            logger.info(f"Response: {response}")
            return typing.cast(dict[str, Any], response)

        except ClientError as e:
            logger.error(f"Error encountered during deleting an object: {e}")
            raise RuntimeError(f"Deleting object {key} from S3 bucket {bucket_name} not successful") from e

    async def get_object_from_bucket(self, bucket_name: str, key: str) -> dict[str, Any]:
        """Retrieves and object from the S3 bucket"""
        try:
            logger.info(f"Retrieving object from S3 bucket {bucket_name} using key: {key}")
            async with self.session_manager.session.client("s3", region_name=self.session_manager.region) as client:
                response = await client.get_object(
                    Bucket=bucket_name,
                    Key=key,
                )
                logger.info(f"Response: {response}")
                return typing.cast(dict[str, Any], response)
        except ClientError as e:
            logger.error(f"Error encountered during getting an object: {e}")
            raise RuntimeError(f"Retrieving object {key} from S3 bucket {bucket_name} not successful") from e

    async def object_exists(self, bucket_name: str, key: str) -> bool:
        try:
            logger.info(f"Checking if key: {key} present in bucket {bucket_name}")
            async with self.session_manager.session.client("s3", region_name=self.session_manager.region) as client:
                await client.head_object(Bucket=bucket_name, Key=key)
                return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise

    async def upload_file_to_bucket(self, bucket_name: str, buffer: BytesIO, key: str) -> bool:
        """
        Uploads a file to a bucket. Sets the stream posiiton to 0, to rewind to the
        start of the stream. (after writing to buffer stream position is at the end,
        so we must set it back to 0 to obtain all of the data)

        :bucket_name: Name of the S3 bucket to be created
        :buffer: An BytesIO buffer with data converted to bytes e.g. PDF file
        :key: The name of the key to upload to. Each object in Amazon S3 has a set of
        key-value pairs
        :return: True if file was uploaded to a bucket, else False
        """
        try:
            buffer.seek(0)
            async with self.session_manager.session.client("s3", region_name=self.session_manager.region) as client:
                await client.upload_fileobj(buffer, bucket_name, key)
            return True
        except ClientError as e:
            logger.error(f"Error encountered during uploading file to a bucket: {e}")
            return False

    async def generate_presigned_url(
        self, client_method: str, method_parameters: dict[str, Any], expires_in: int
    ) -> Any:
        """
        Generates a presigned URL for the given S3 client method and parameters.
        :client_method: The S3 client method for which to generate the presigned URL
        (e.g., "get_object", "put_object")
        :method_parameters: A dictionary of parameters to be passed to the S3 client method
        (e.g., {"Bucket": ..., "Key": ...})
        :expires_in: The time in seconds for which the presigned URL is valid
        Example: await client.generate_presigned_url("get_object", Params={"Bucket": ..., "Key": ...},
        ExpiresIn=300)
        """
        try:
            logger.info(
                f"Generating presigned URL for client method: {client_method} with parameters: "
                f"{method_parameters} and expiration time: {expires_in} seconds"
            )
            async with self.session_manager.session.client("s3", region_name=self.session_manager.region) as client:
                response = await client.generate_presigned_url(
                    ClientMethod=client_method, Params=method_parameters, ExpiresIn=expires_in
                )
            logger.info(f"Got presigned URL: {response}")
        except ClientError as e:
            logger.error(f"Couldn't get a presigned URL for client method: {client_method}. Error: {e}")
            raise
        return response

    async def head_object(self, bucket_name: str, key: str) -> dict[str, Any]:
        """Checks if an object exists in the S3 bucket by sending a HEAD request"""
        try:
            logger.info(f"Checking if object exists in S3 bucket {bucket_name} using key: {key}")
            async with self.session_manager.session.client("s3", region_name=self.session_manager.region) as client:
                response = await client.head_object(
                    Bucket=bucket_name,
                    Key=key,
                )
            logger.info(f"Response: {response}")
            return typing.cast(dict[str, Any], response)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                logger.info(f"Object with key {key} not found in bucket {bucket_name}.")
                return {}
            logger.error(f"Error encountered during checking if object exists: {e}")
            raise RuntimeError(f"Checking if object {key} exists in S3 bucket {bucket_name} not successful") from e
