from aws_helpers import EC2_RESOURCE, CLOUDWATCH_RESOURCE, make_str_unique
import boto3

class Alarm:
    def __init__(self, metric, period, eval_periods, stat, threshold, comparison):
        self.metric = metric
        self.period = period
        self.eval_periods = eval_periods
        self.stat = stat
        self.threshold = threshold
        self.comparison = comparison

    def create_ec2_alarm(self, metric_name, instance_id):
        metric = CLOUDWATCH_RESOURCE.Metric('AWS/EC2', metric_name)
        alarm = metric.put_alarm(
            AlarmName=make_str_unique(metric_name),
            AlarmDescription=f"Triggered when {metric_name} {self.comparison} {self.threshold} for {self.eval_periods} consecutive {self.period // 60}-minute periods",
            ActionsEnabled=True,
            AlarmActions=['arn:aws:automate:us-east-2:ec2:reboot'],
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            Period=self.period,
            EvaluationPeriods=self.eval_periods,
            Statistic=self.stat,
            Threshold=self.threshold,
            ComparisonOperator=self.comparison,
        )

try:
	outfile = open('../.env/ec2keypair.pem', 'w')
	key_pair = EC2_RESOURCE.create_key_pair(KeyName='ec2keypair')
	KeyPairOut = str(key_pair.key_material)
	print(KeyPairOut)
	outfile.write(KeyPairOut)
	outfile.close()
except:
	print("Using existing ec2keypair.")

# Creating New Security Group
try:
	print("Creating New Security Group...")
	mysg = EC2_RESOURCE.create_security_group(
		GroupName='http&ssh',
		Description='security group allowing http, ssh and ping')
	mysg.authorize_ingress(
		IpPermissions=[
			{'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80,
			 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
			{'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22,
			 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
			{'IpProtocol': 'icmp', 'FromPort': 8, 'ToPort': -1,
			 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
		])
	print('security group is created')
except:
	print("Using existing http&ssh security group.")

# Launching New EC2 Instance
print("Launching New EC2 Instance...")
instances = EC2_RESOURCE.create_instances(
    ImageId='ami-0e68dc81dc36750a1',
    MinCount=1,
    MaxCount=1,
    InstanceType='t2.micro',
    KeyName='ec2keypair',
    SecurityGroups=['http&ssh'],
    BlockDeviceMappings=[{"DeviceName": "/dev/xvda",
        "Ebs": {"VolumeSize": 8}}]
)

i = instances[0]
print('instance', i.id, 'is created')
i.wait_until_running()
print('instance', i.id, 'is running')

EC2_RESOURCE.meta.client.create_tags(Resources=[i.id],
    Tags=[{'Key': 'Name', 'Value': make_str_unique('lecture6-instance')}])

instance_id = i.id

for alarm_metric in ['StatusCheckFailed', 'StatusCheckFailed_System', 'StatusCheckFailed_Instance']:
    a = Alarm(alarm_metric, 60, 1, 'Average', 0.99, 'GreaterThanOrEqualToThreshold')
    a.create_ec2_alarm(alarm_metric, instance_id)
