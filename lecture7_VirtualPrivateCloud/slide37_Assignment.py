from aws_helpers import EC2_RESOURCE, region_name

print("Creating New VPC...")
vpc = EC2_RESOURCE.create_vpc(CidrBlock='10.2.0.0/16')
vpc.wait_until_available()
vpc.modify_attribute(EnableDnsHostnames={'Value': True})
vpc.create_tags(Tags=[{'Key': 'Name', 'Value': 'Lecture7-Python-vpc'}])
print('vpc is created', vpc.id)

print("Creating New Internet Gateway...")
internet_gateway = EC2_RESOURCE.create_internet_gateway()
vpc.attach_internet_gateway(InternetGatewayId=internet_gateway.id)
internet_gateway.create_tags(Tags=[{'Key': 'Name', 'Value': 'Lecture7-Python-igw'}])
print('internet gateway is created', internet_gateway.id)

print("Creating New Route Tables...")
public_route_table = vpc.create_route_table()
public_route_table.create_tags(Tags=[{'Key': 'Name', 'Value': 'Lecture7-Python-rtb-public'}])
public_route_table.create_route(
	DestinationCidrBlock='0.0.0.0/0',
	GatewayId=internet_gateway.id
)
print('public route table is created', public_route_table.id)

private_route_table = vpc.create_route_table()
private_route_table.create_tags(Tags=[{'Key': 'Name', 'Value': f'Lecture7-Python-rtb-private1-{region_name}a'}])
print('private route table is created', private_route_table.id)

print("Creating New Subnets...")
public_subnet = EC2_RESOURCE.create_subnet(
	CidrBlock='10.2.0.0/20',
	AvailabilityZone=f'{region_name}a',
	VpcId=vpc.id
)
public_subnet.create_tags(Tags=[{'Key': 'Name', 'Value': f'Lecture7-Python-subnet-public1-{region_name}a'}])
public_route_table.associate_with_subnet(SubnetId=public_subnet.id)
print('public subnet is created', public_subnet.id)

private_subnet = EC2_RESOURCE.create_subnet(
	CidrBlock='10.2.128.0/20',
	AvailabilityZone=f'{region_name}a',
	VpcId=vpc.id
)
private_subnet.create_tags(Tags=[{'Key': 'Name', 'Value': f'Lecture7-Python-subnet-private1-{region_name}a'}])
private_route_table.associate_with_subnet(SubnetId=private_subnet.id)
print('private subnet is created', private_subnet.id)

print("Creating New Public Security Group...")
public_sg = EC2_RESOURCE.create_security_group(
	GroupName='Lecture7-Public-Python',
	Description='Allow port 80 for Lecture 7',
	VpcId=vpc.id
)
public_sg.authorize_ingress(
	IpPermissions=[
		{'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80,
		 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
	])
print('public security group is created', public_sg.id)

print("Creating New Private Security Group...")
private_sg = EC2_RESOURCE.create_security_group(
	GroupName='Lecture7-Private-Python',
	Description='Allow traffic from VPC for Lecture 7',
	VpcId=vpc.id
)
private_sg.authorize_ingress(
	IpPermissions=[
		{'IpProtocol': 'tcp', 'FromPort': 0, 'ToPort': 65535,
		 'IpRanges': [{'CidrIp': vpc.cidr_block}]}
	])
print('private security group is created', private_sg.id)

print("Launching New Public EC2 Instance...")
public_instances = EC2_RESOURCE.create_instances(
	ImageId='ami-0e68dc81dc36750a1',
	MinCount=1,
	MaxCount=1,
	InstanceType='t2.micro',
	KeyName='debian',
	NetworkInterfaces=[{
		'SubnetId': public_subnet.id,
		'DeviceIndex': 0,
		'AssociatePublicIpAddress': True,
		'Groups': [public_sg.id],
	}],
)
public_instance = public_instances[0]
print('instance', public_instance.id, 'is created')
public_instance.wait_until_running()
print('instance', public_instance.id, 'is running')
public_instance.create_tags(Tags=[{'Key': 'Name', 'Value': 'Lecture7-PublicInstance-Python'}])

print("Launching New Private EC2 Instance...")
private_instances = EC2_RESOURCE.create_instances(
	ImageId='ami-0e68dc81dc36750a1',
	MinCount=1,
	MaxCount=1,
	InstanceType='t2.micro',
	KeyName='debian',
	NetworkInterfaces=[{
		'SubnetId': private_subnet.id,
		'DeviceIndex': 0,
		'AssociatePublicIpAddress': False,
		'Groups': [private_sg.id],
	}],
)
private_instance = private_instances[0]
print('instance', private_instance.id, 'is created')
private_instance.wait_until_running()
print('instance', private_instance.id, 'is running')
private_instance.create_tags(Tags=[{'Key': 'Name', 'Value': 'Lecture7-PrivateInstance-Python'}])

public_instance.reload()
private_instance.reload()
print('public instance public ip:', public_instance.public_ip_address)
print('private instance public ip:', private_instance.public_ip_address)
