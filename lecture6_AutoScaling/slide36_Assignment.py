from aws_helpers import EC2_RESOURCE, CLOUDWATCH_RESOURCE, AUTOSCALING_CLIENT, make_str_unique, region_name

ec2_client = EC2_RESOURCE.meta.client

print("Finding Security Group...")
response = ec2_client.describe_security_groups(
	Filters=[{'Name': 'group-name', 'Values': ['http&ssh']}]
)
security_group_id = response['SecurityGroups'][0]['GroupId']

print("Creating New Launch Template...")
launch_template = ec2_client.create_launch_template(
	LaunchTemplateData={
		'ImageId': 'ami-0e68dc81dc36750a1',
		'InstanceType': 't2.micro',
		'KeyName': 'debian',
		'SecurityGroupIds': [security_group_id],
	},
	LaunchTemplateName='Lecture6-Template-Python',
)
print('launch template is created')

print("Creating New Auto Scaling Group...")
AUTOSCALING_CLIENT.create_auto_scaling_group(
	AutoScalingGroupName='Lecture6-Group-Python',
	LaunchTemplate={'LaunchTemplateName': 'Lecture6-Template-Python'},
	MinSize=1,
	MaxSize=3,
	DesiredCapacity=1,
	AvailabilityZones=[f'{region_name}a'],
)
print('auto scaling group is created')

print("Creating New Scaling Policy...")
policy_response = AUTOSCALING_CLIENT.put_scaling_policy(
	AutoScalingGroupName='Lecture6-Group-Python',
	PolicyName='Lecture6-ScaleUp-Python',
	PolicyType='SimpleScaling',
	AdjustmentType='ChangeInCapacity',
	ScalingAdjustment=1,
	Cooldown=300,
	Enabled=True,
)
simple_scale_arn = policy_response['PolicyARN']
print('scaling policy is created')

print("Creating New Status Check Alarm...")
metric = CLOUDWATCH_RESOURCE.Metric('AWS/EC2', 'StatusCheckFailed')
metric.put_alarm(
	AlarmName=make_str_unique('Lecture6-GroupStatusCheck-Python'),
	AlarmDescription='Trigger alarm when the auto scaling group status check fails',
	ActionsEnabled=True,
	AlarmActions=[simple_scale_arn],
	Dimensions=[{'Name': 'AutoScalingGroupName', 'Value': 'Lecture6-Group-Python'}],
	Period=60,
	EvaluationPeriods=1,
	Statistic='Average',
	Threshold=0.99,
	ComparisonOperator='GreaterThanOrEqualToThreshold',
)
print('status check alarm is created')
