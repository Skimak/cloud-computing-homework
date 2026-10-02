import os
import sys
import time
import random
import json
import string
import boto3
import configparser

creds = configparser.ConfigParser()
creds_path = '~/.aws/credentials'
creds_read = creds.read(os.path.expanduser(creds_path))

region_name = 'us-east-2'

if not creds_read:
	sys.exit(f"Could not read credentials from {creds_path}.")

def create_handle(service, handle_creation_callback):
	return handle_creation_callback(
		service,
		aws_access_key_id=creds['default']['aws_access_key_id'],
		aws_secret_access_key=creds['default']['aws_secret_access_key'],
		region_name=region_name
	)

def create_resource(service):
	return create_handle(service, boto3.resource)

def create_client(service):
	return create_handle(service, boto3.client)

S3_RESOURCE = create_resource('s3')
S3_CLIENT = create_client('s3') 
EC2_RESOURCE = create_resource('ec2')
CLOUDWATCH_RESOURCE = create_resource('cloudwatch')

def get_buckets():
	return S3_RESOURCE.buckets.all()

def enable_public_bucket_access(bucket_name):
	S3_CLIENT.put_public_access_block(
		Bucket=bucket_name,
		PublicAccessBlockConfiguration={
			'BlockPublicAcls': False,
			'IgnorePublicAcls': False,
			'BlockPublicPolicy': False,
			'RestrictPublicBuckets': False
		}
	)

	time.sleep(2)

	policy_payload = {
		"Version": "2012-10-17",
		"Statement": [
			{
				"Sid": "MakeItPublic",
				"Effect": "Allow",
				"Principal": "*",
				"Action": "s3:GetObject",
				"Resource": "arn:aws:s3:::%s/*" % bucket_name
			}
		]
	}

	S3_CLIENT.put_bucket_policy(Bucket=bucket_name,
		Policy=json.dumps(policy_payload))

def make_str_unique(original_str):
	unique_str = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
	return f"{original_str}-{unique_str}"

__all__ = [
	'S3_RESOURCE', 'S3_CLIENT', 'get_buckets',
	'EC2_RESOURCE',
	'CLOUDWATCH_RESOURCE',
	'make_str_unique'
]
