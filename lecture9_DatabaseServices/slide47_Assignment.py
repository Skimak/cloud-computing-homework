from aws_helpers import DYNAMODB_RESOURCE
from boto3.dynamodb.conditions import Key, Attr

print("Creating New Table...")
table = DYNAMODB_RESOURCE.create_table(
	TableName='Lecture9-Students-Python',
	KeySchema=[
		{'AttributeName': 'Name', 'KeyType': 'HASH'},
		{'AttributeName': 'StudentId', 'KeyType': 'RANGE'},
	],
	AttributeDefinitions=[
		{'AttributeName': 'Name', 'AttributeType': 'S'},
		{'AttributeName': 'StudentId', 'AttributeType': 'N'},
	],
	BillingMode='PAY_PER_REQUEST',
)
table.meta.client.get_waiter('table_exists').wait(TableName='Lecture9-Students-Python')
print('table is created')

print("Adding Students...")
table.put_item(Item={'Name': 'Alice', 'StudentId': 1, 'Major': 'Computer Science'})
table.put_item(Item={'Name': 'Bob', 'StudentId': 2, 'Major': 'Engineering'})
table.put_item(Item={'Name': 'Alan', 'StudentId': 3, 'Major': 'Communications'})
table.put_item(Item={'Name': 'Joe', 'StudentId': 4, 'Major': 'Physics'})
table.put_item(Item={'Name': 'John', 'StudentId': 5, 'Major': 'Criminology'})
print('5 students are added')

print("Querying Student Named Bob...")
response = table.query(
	KeyConditionExpression=Key('Name').eq('Bob'),
)
for item in response['Items']:
	print(item['Name'], item['StudentId'], item['Major'])

print("Scanning Student Named Alice...")
response = table.scan(FilterExpression=Attr('Name').eq('Alice'))

for item in response['Items']:
	print(item['Name'], item['StudentId'], item['Major'])
