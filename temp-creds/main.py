import asyncio
import aioboto3
from botocore.exceptions import ClientError
import json


async def generate_temporary_credentials(bucket_name, prefix, duration_seconds=3600):
    role_arn = "arn:aws:iam::151312473579:role/STSReadCredsRoleStaging"
    session_name = "TemporaryAccessSession"

    session = aioboto3.Session()
    try:
        async with session.client('sts') as sts_client:
            response = await sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName=session_name,
                DurationSeconds=duration_seconds
            )

            credentials = response['Credentials']
            return {
                "AccessKeyId": credentials['AccessKeyId'],
                "SecretAccessKey": credentials['SecretAccessKey'],
                "SessionToken": credentials['SessionToken'],
                "Expiration": credentials['Expiration']
            }
    except ClientError as e:
        print(f"Error generating temporary credentials: {e}")
        return None


async def list_files_in_s3(bucket_name, prefix, credentials):
    session = aioboto3.Session()
    try:
        async with session.client(
            's3',
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken']
        ) as s3_client:
            paginator = s3_client.get_paginator('list_objects_v2')
            async for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
                for obj in page.get('Contents', []):
                    print(obj['Key'])
    except ClientError as e:
        print(f"Error listing files in S3: {e}")


async def main():
    bucket_name = "linc-brain-mit-staging-us-east-2"
    prefix = "zarr/"
    duration_seconds = 3600  # 1 hour

    credentials = await generate_temporary_credentials(bucket_name, prefix, duration_seconds)
    if credentials:
        print("Temporary Credentials:")
        print(json.dumps(credentials, indent=4, default=str))
        print("\nListing files in the bucket:\n")
        await list_files_in_s3(bucket_name, prefix, credentials)
    else:
        print("Failed to generate credentials.")


if __name__ == "__main__":
    asyncio.run(main())