from aws_helpers import EC2_RESOURCE, AUTOSCALING_CLIENT, ELB_CLIENT, region_name

print("Creating New VPC...")
vpc = EC2_RESOURCE.create_vpc(CidrBlock='10.4.0.0/16')
vpc.wait_until_available()
vpc.modify_attribute(EnableDnsHostnames={'Value': True})
vpc.create_tags(Tags=[{'Key': 'Name', 'Value': 'Lecture8-Python-vpc'}])
print('vpc is created', vpc.id)

print("Creating New Internet Gateway...")
internet_gateway = EC2_RESOURCE.create_internet_gateway()
vpc.attach_internet_gateway(InternetGatewayId=internet_gateway.id)
internet_gateway.create_tags(Tags=[{'Key': 'Name', 'Value': 'Lecture8-Python-igw'}])
print('internet gateway is created', internet_gateway.id)

print("Creating New Route Table...")
public_route_table = vpc.create_route_table()
public_route_table.create_tags(Tags=[{'Key': 'Name', 'Value': 'Lecture8-Python-rtb-public'}])
public_route_table.create_route(
	DestinationCidrBlock='0.0.0.0/0',
	GatewayId=internet_gateway.id
)
print('public route table is created', public_route_table.id)

print("Creating New Subnets...")
public_subnet1 = EC2_RESOURCE.create_subnet(
	CidrBlock='10.4.0.0/20',
	AvailabilityZone=f'{region_name}a',
	VpcId=vpc.id
)
public_subnet1.create_tags(Tags=[{'Key': 'Name', 'Value': f'Lecture8-Python-subnet-public1-{region_name}a'}])
public_route_table.associate_with_subnet(SubnetId=public_subnet1.id)
print('public subnet 1 is created', public_subnet1.id)

public_subnet2 = EC2_RESOURCE.create_subnet(
	CidrBlock='10.4.16.0/20',
	AvailabilityZone=f'{region_name}b',
	VpcId=vpc.id
)
public_subnet2.create_tags(Tags=[{'Key': 'Name', 'Value': f'Lecture8-Python-subnet-public2-{region_name}b'}])
public_route_table.associate_with_subnet(SubnetId=public_subnet2.id)
print('public subnet 2 is created', public_subnet2.id)

print("Creating New Security Group...")
ssh_sg = EC2_RESOURCE.create_security_group(
	GroupName='Lecture8-SSH-Python',
	Description='Allow SSH for Lecture 8',
	VpcId=vpc.id
)
ssh_sg.authorize_ingress(
	IpPermissions=[
		{'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22,
		 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
	])
print('security group is created', ssh_sg.id)

print("Creating New Launch Template...")
EC2_RESOURCE.meta.client.create_launch_template(
	LaunchTemplateData={
		'ImageId': 'ami-0e68dc81dc36750a1',
		'InstanceType': 't2.micro',
		'KeyName': 'debian',
		'SecurityGroupIds': [ssh_sg.id],
	},
	LaunchTemplateName='Lecture8-Template-Python',
)
print('launch template is created')

print("Creating New Target Group...")
response = ELB_CLIENT.create_target_group(
	Name='Lecture8-TargetGroup-Python',
	Protocol='TCP',
	Port=22,
	TargetType='instance',
	VpcId=vpc.id
)
target_group_arn = response['TargetGroups'][0]['TargetGroupArn']
print('target group is created')

print("Creating New Network Load Balancer...")
response = ELB_CLIENT.create_load_balancer(
	Name='Lecture8-LoadBalancer-Python',
	Scheme='internet-facing',
	Type='network',
	Subnets=[public_subnet1.id, public_subnet2.id],
)
load_balancer = response['LoadBalancers'][0]
load_balancer_arn = load_balancer['LoadBalancerArn']
print('load balancer is created', load_balancer['DNSName'])

print("Creating New Listener...")
ELB_CLIENT.create_listener(
	LoadBalancerArn=load_balancer_arn,
	Port=22,
	Protocol='TCP',
	DefaultActions=[{'TargetGroupArn': target_group_arn, 'Type': 'forward'}]
)
print('listener is created')

print("Creating New Auto Scaling Group...")
AUTOSCALING_CLIENT.create_auto_scaling_group(
	AutoScalingGroupName='Lecture8-Group-Python',
	LaunchTemplate={'LaunchTemplateName': 'Lecture8-Template-Python'},
	MinSize=2,
	MaxSize=3,
	DesiredCapacity=2,
	VPCZoneIdentifier=f'{public_subnet1.id},{public_subnet2.id}',
)
print('auto scaling group is created')

print("Attaching Target Group to Auto Scaling Group...")
AUTOSCALING_CLIENT.attach_load_balancer_target_groups(
	AutoScalingGroupName='Lecture8-Group-Python',
	TargetGroupARNs=[target_group_arn]
)
print('target group is attached')
