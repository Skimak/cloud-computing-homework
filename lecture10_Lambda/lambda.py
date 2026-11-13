import json
import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

def lambda_handler(event, context):
	ddb = boto3.resource('dynamodb')
	table = ddb.Table('Lecture9-Students-Python')

	raw_path = event.get('rawPath', '')

	if raw_path == '/get_data':
		query_params = event.get('queryStringParameters') or {}

		if not query_params:
			return {
				'statusCode': 400,
				'headers': {
					'Content-Type': 'application/json',
					'Access-Control-Allow-Origin': '*'
				},
				'body': json.dumps({'error': 'Missing query parameters'})
			}

		keys = list(query_params.keys())
		key = str(keys[0])
		value = str(query_params[key])

		try:
			if key == 'StudentId':
				value = int(value)

			result = []
			response = table.scan(FilterExpression=Attr(key).eq(value))

			for item in response.get('Items', []):
				# Using .get() prevents KeyError if fields are occasionally missing
				student_id = str(item.get('StudentId', 'Unknown StudentId'))
				name = str(item.get('Name', 'Unknown Name'))
				major = str(item.get('Major', 'Unknown Major'))
				result.append(f"#{student_id}: {name}, {major}")
			return {
				'statusCode': 200,
				'headers': {
					'Content-Type': 'application/json',
					'Access-Control-Allow-Origin': '*',
					'Access-Control-Allow-Methods': 'GET, OPTIONS'
				},
				'body': json.dumps(result)
			}
		except (ClientError, ValueError) as e:
			return {
				'statusCode': 500,
				'headers': {
					'Content-Type': 'application/json',
					'Access-Control-Allow-Origin': '*'
				},
				'body': json.dumps(str(e))
			}

	if raw_path == '/add_data':
		try:
			# Handle missing or empty request body safely
			body_str = event.get('body', '{}')
			body = json.loads(body_str) if body_str else {}

			student_id = body.get('StudentId')
			name = body.get('Name')
			major = body.get('Major')

			if not student_id or not name or not major:
				return {
					'statusCode': 400,
					'headers': {
						'Content-Type': 'application/json',
						'Access-Control-Allow-Origin': '*'
					},
					'body': json.dumps({'error': 'StudentId, Name and Major are required'})
				}

			table.put_item(
				Item={'StudentId': int(student_id), 'Name': name, 'Major': major}
			)
			result = f"#{student_id}: {name}, {major} added successfully!"
			return {
				'statusCode': 200,
				'headers': {
					'Content-Type': 'application/json',
					'Access-Control-Allow-Origin': '*',
					'Access-Control-Allow-Methods': 'POST, OPTIONS'
				},
				'body': json.dumps(result)
			}

		except (ClientError, json.JSONDecodeError, ValueError) as e:
			return {
				'statusCode': 500,
				'headers': {
					'Content-Type': 'application/json',
					'Access-Control-Allow-Origin': '*'
				},
				'body': json.dumps(str(e))
			}

	# Fallback default response for unsupported routes
	return {
		'statusCode': 404,
		'headers': {
			'Content-Type': 'application/json',
			'Access-Control-Allow-Origin': '*'
		},
		'body': json.dumps({'error': 'Not Found'})
	}
