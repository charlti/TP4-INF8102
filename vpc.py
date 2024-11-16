import boto3
from troposphere import Template, Ref, Tags, Join, Sub, Select, GetAZs, GetAtt, Parameter, Output
from troposphere.ec2 import (
    VPC,
    Subnet,
    RouteTable,
    InternetGateway,
    VPCGatewayAttachment,
    NatGateway,
    EIP,
    Route,
    SubnetRouteTableAssociation,
    SecurityGroup,
    SecurityGroupRule
)

# Créer un template Troposphere
template = Template()
template.set_description("CloudFormation template generated via Troposphere")

############ Paramètres ############

environment_name = template.add_parameter(
    Parameter(
        "EnvironmentName",
        Type="String",
        Description="Environment is prefixed to resource names",
        Default="PolyEnvironment"
    )
)

vpc_cidr = template.add_parameter(
    Parameter(
        "VpcCIDR",
        Description="VPC polystudent-vpc",
        Type="String",
        Default="10.0.0.0/16"
    )
)

public_subnet1_cidr = template.add_parameter(
    Parameter(
        "PublicSubnet1CIDR",
        Description="public subnet in Availability Zone 1",
        Type="String",
        Default="10.0.0.0/24"
    )
)

public_subnet2_cidr = template.add_parameter(
    Parameter(
        "PublicSubnet2CIDR",
        Description="Public Subnet in availability zone 2",
        Type="String",
        Default="10.0.16.0/24"
    )
)

private_subnet1_cidr = template.add_parameter(
    Parameter(
        "PrivateSubnet1CIDR",
        Description="Private Subnet in availability zone 1",
        Type="String",
        Default="10.0.128.0/24"
    )
)

private_subnet2_cidr = template.add_parameter(
    Parameter(
        "PrivateSubnet2CIDR",
        Description="Private Subnet in availability zone 2",
        Type="String",
        Default="10.0.144.0/24"
    )
)

############ Ressources ############

# VPC
vpc = template.add_resource(
    VPC(
        "VPC",
        CidrBlock=Ref(vpc_cidr),
        EnableDnsSupport=True,
        EnableDnsHostnames=True,
        Tags=Tags(Name=Ref(environment_name)),
    )
)

# Internet Gateway
internet_gateway = template.add_resource(
    InternetGateway(
        "InternetGateway",
        Tags=Tags(Name=Ref(environment_name))
    )
)

gateway_attachment = template.add_resource(
    VPCGatewayAttachment(
        "InternetGatewayAttachment",
        VpcId=Ref(vpc),
        InternetGatewayId=Ref(internet_gateway),
    )
)

# Public Subnets
public_subnet1 = template.add_resource(
    Subnet(
        "PublicSubnet1",
        VpcId=Ref(vpc),
        AvailabilityZone=Select(0, GetAZs("")),
        CidrBlock=Ref(public_subnet1_cidr),
        MapPublicIpOnLaunch=True,
        Tags=Tags(Name=Sub("${EnvironmentName} Public Subnet (AZ1)")),
    )
)

public_subnet2 = template.add_resource(
    Subnet(
        "PublicSubnet2",
        VpcId=Ref(vpc),
        AvailabilityZone=Select(1, GetAZs("")),
        CidrBlock=Ref(public_subnet2_cidr),
        MapPublicIpOnLaunch=True,
        Tags=Tags(Name=Sub("${EnvironmentName} Public Subnet (AZ2)")),
    )
)

# Private Subnets
private_subnet1 = template.add_resource(
    Subnet(
        "PrivateSubnet1",
        VpcId=Ref(vpc),
        AvailabilityZone=Select(0, GetAZs("")),
        CidrBlock=Ref(private_subnet1_cidr),
        MapPublicIpOnLaunch=False,
        Tags=Tags(Name=Sub("${EnvironmentName} Private Subnet (AZ1)")),
    )
)

private_subnet2 = template.add_resource(
    Subnet(
        "PrivateSubnet2",
        VpcId=Ref(vpc),
        AvailabilityZone=Select(1, GetAZs("")),
        CidrBlock=Ref(private_subnet2_cidr),
        MapPublicIpOnLaunch=False,
        Tags=Tags(Name=Sub("${EnvironmentName} Private Subnet (AZ2)")),
    )
)

# Public Route Table

public_route_table = template.add_resource(
    RouteTable(
        "PublicRouteTable",
        VpcId=Ref(vpc),
        Tags=Tags(Name=Sub("${EnvironmentName} Public Routes"))
    )
)

# Nat Gateways

nat_gateway_eip1 = template.add_resource(
    EIP(
        "NatGateway1EIP",
        DependsOn="InternetGatewayAttachment",
        Domain="vpc"
    )
)

nat_gateway_eip2 = template.add_resource(
    EIP(
        "NatGateway2EIP",
        DependsOn="InternetGatewayAttachment",
        Domain="vpc"
    )
)

nat_gateway_1 = template.add_resource(
    NatGateway(
        "NatGateway1",
        AllocationId=GetAtt(nat_gateway_eip1, "AllocationId"),
        SubnetId=Ref(public_subnet1)
    )
)

nat_gateway_2 = template.add_resource(
    NatGateway(
        "NatGateway2",
        AllocationId=GetAtt(nat_gateway_eip2, "AllocationId"),
        SubnetId=Ref(public_subnet2)
    )
)

# Routes

default_public_route = template.add_resource(
    Route(
        "DefaultPublicRoute",
        DependsOn="InternetGatewayAttachment",
        RouteTableId=Ref(public_route_table),
        DestinationCidrBlock="0.0.0.0/0",
        GatewayId=Ref(internet_gateway)
    )
)

public_subnet1_route_table_association = template.add_resource(
    SubnetRouteTableAssociation(
        "PublicSubnet1RouteTableAssociation",
        RouteTableId=Ref(public_route_table),
        SubnetId=Ref(public_subnet1)
    )
)

public_subnet2_route_table_association = template.add_resource(
    SubnetRouteTableAssociation(
        "PublicSubnet2RouteTableAssociation",
        RouteTableId=Ref(public_route_table),
        SubnetId=Ref(public_subnet2)
    )
)

private_route_table1 = template.add_resource(
    RouteTable(
        "PrivateRouteTable1",
        VpcId=Ref(vpc),
        Tags=Tags(Name=Sub("${EnvironmentName} Private Routes (AZ1)"))
    )
)

default_private_route1 = template.add_resource(
    Route(
        "DefaultPrivateRoute1",
        RouteTableId=Ref(private_route_table1),
        DestinationCidrBlock="0.0.0.0/0",
        NatGatewayId=Ref(nat_gateway_1)
    )
)

private_subnet1_route_table_association = template.add_resource(
    SubnetRouteTableAssociation(
        "PrivateSubnet1RouteTableAssociation",
        RouteTableId=Ref(private_route_table1),
        SubnetId=Ref(private_subnet1)
    )
)

private_route_table2 = template.add_resource(
    RouteTable(
        "PrivateRouteTable2",
        VpcId=Ref(vpc),
        Tags=Tags(Name=Sub("${EnvironmentName} Private Routes (AZ2)"))
    )
)

default_private_route2 = template.add_resource(
    Route(
        "DefaultPrivateRoute2",
        RouteTableId=Ref(private_route_table2),
        DestinationCidrBlock="0.0.0.0/0",
        NatGatewayId=Ref(nat_gateway_2)
    )
)

private_subnet2_route_table_association = template.add_resource(
    SubnetRouteTableAssociation(
        "PrivateSubnet2RouteTableAssociation",
        RouteTableId=Ref(private_route_table2),
        SubnetId=Ref(private_subnet2)
    )
)

# Security Group

ingress_rules = [
    {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22, "CidrIp": "0.0.0.0/0"},
    {"IpProtocol": "tcp", "FromPort": 80, "ToPort": 80, "CidrIp": "0.0.0.0/0"},
    {"IpProtocol": "tcp", "FromPort": 443, "ToPort": 443, "CidrIp": "0.0.0.0/0"},
    {"IpProtocol": "tcp", "FromPort": 53, "ToPort": 53, "CidrIp": "0.0.0.0/0"},
    {"IpProtocol": "udp", "FromPort": 53, "ToPort": 53, "CidrIp": "0.0.0.0/0"},
    {"IpProtocol": "tcp", "FromPort": 1433, "ToPort": 1433, "CidrIp": "0.0.0.0/0"},
    {"IpProtocol": "tcp", "FromPort": 5432, "ToPort": 5432, "CidrIp": "0.0.0.0/0"},
    {"IpProtocol": "tcp", "FromPort": 3306, "ToPort": 3306, "CidrIp": "0.0.0.0/0"},
    {"IpProtocol": "tcp", "FromPort": 3389, "ToPort": 3389, "CidrIp": "0.0.0.0/0"},
    {"IpProtocol": "tcp", "FromPort": 1514, "ToPort": 1514, "CidrIp": "0.0.0.0/0"},
    {"IpProtocol": "tcp", "FromPort": 9200, "ToPort": 9300, "CidrIp": "0.0.0.0/0"}
]

security_group = template.add_resource(
    SecurityGroup(
        "IngressSecurityGroup",
        GroupDescription="Security group allows SSH, HTTP, HTTPS, MSSQL, DNS, PostgreSQL, MySQL, RDP, OSSEC and ElasticSearch",
        GroupName="polystudent-sg",
        VpcId=Ref(vpc),
        SecurityGroupIngress=[SecurityGroupRule(**rule) for rule in ingress_rules]
        
    )
)

############ OUTPUT ############

# VPC Output
template.add_output(
    Output(
        "VPC",
        Description="A reference to the created VPC",
        Value=Ref(vpc)
    )
)

# Public Subnets Output
template.add_output(
    Output(
        "PublicSubnets",
        Description="A list of the public subnets",
        Value=Join(",", [Ref("PublicSubnet1"), Ref("PublicSubnet2")])
    )
)

# Private Subnets Output
template.add_output(
    Output(
        "PrivateSubnets",
        Description="A list of the private subnets",
        Value=Join(",", [Ref(private_subnet1), Ref(private_subnet2)])
    )
)

# Public Subnet 1 Output
template.add_output(
    Output(
        "PublicSubnet1",
        Description="A reference to the public subnet in Availability Zone 1",
        Value=Ref(public_subnet1)
    )
)

# Public Subnet 2 Output
template.add_output(
    Output(
        "PublicSubnet2",
        Description="A reference to the public subnet in Availability Zone 2",
        Value=Ref(public_subnet2)
    )
)

# Private Subnet 1 Output
template.add_output(
    Output(
        "PrivateSubnet1",
        Description="A reference to the private subnet in Availability Zone 1",
        Value=Ref(private_subnet1)
    )
)

# Private Subnet 2 Output
template.add_output(
    Output(
        "PrivateSubnet2",
        Description="A reference to the private subnet in Availability Zone 2",
        Value=Ref(private_subnet2)
    )
)

with open('vpc_final.yml', 'w') as f:
    f.write(template.to_yaml())

print("Template yml bien généré dans le fichier")


with open('vpc_final.yml', 'r') as template:
    template_body = template.read()


access_key = 'your_access_key'
secret_key = 'your_secret_key'
region = 'your_region'

cloudformation = boto3.client('cloudformation', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)
stack_name = 'PolyStack'


# Essayer de créer une nouvelle stack
response = cloudformation.create_stack(
    StackName=stack_name,
    TemplateBody=template_body,
)
print("Stack creation initiated:", response)
