import boto3
from troposphere import Template, Ref, Tags, Join, Sub, Select, GetAZs, GetAtt, Parameter, Output, cloudwatch
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
    SecurityGroupRule,
    FlowLog,
    Instance,
    BlockDeviceMapping,
    EBSBlockDevice
)

from troposphere.s3 import BucketPolicy
from troposphere.sns import Topic, Subscription

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
"""
s3_bucket_name = template.add_parameter(
    Parameter(
        "S3BucketName",
        Type="String",
        Description="Name of the S3 bucket for VPC Flow Logs",
        Default="polystudentsbucket"  # Le nom du bucket créé précédemment
    )
)
"""
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

"""
vpc_flow_log = template.add_resource(
    FlowLog(
        "VPCFlowLog",
        # Supprimer la ligne DeliverLogsPermissionArn
        LogDestination=Sub("arn:aws:s3:::${S3BucketName}"),
        LogDestinationType="s3",
        ResourceId=Ref(vpc),
        ResourceType="VPC",
        TrafficType="REJECT",
        MaxAggregationInterval=600,
        Tags=Tags(
            Name=Sub("${EnvironmentName}-flow-logs")
        )
    )
)
"""
"""
bucket_policy = template.add_resource(
    BucketPolicy(
        "S3BucketPolicy",
        Bucket=Ref(s3_bucket_name),  # Référence au nom du bucket
        PolicyDocument={
            "Version": "2012-10-17",
            "Statement": [{
                "Sid": "AWSVPCFlowLogs",
                "Effect": "Allow",
                "Principal": {
                    "Service": "delivery.logs.amazonaws.com"
                },
                "Action": "s3:PutObject",
                "Resource": Sub("arn:aws:s3:::${S3BucketName}/*"),
                "Condition": {
                    "StringEquals": {
                        "s3:x-amz-acl": "bucket-owner-full-control"
                    }
                }
            }]
        }
    )
)
"""
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


ec2_public_instance1 = template.add_resource(
    Instance(
    "EC2PublicInstance1",
    KeyName="polystudent-pair",
    InstanceType="t2.micro",
    ImageId="ami-0eb9fdcf0d07bd5ef",
    AvailabilityZone="ca-central-1a",
    SecurityGroupIds=[Ref(security_group)],
    SubnetId=Ref(public_subnet1),
    IamInstanceProfile="iam-instances",
    BlockDeviceMappings=[
        BlockDeviceMapping(
            DeviceName="/dev/sda1",
            Ebs=EBSBlockDevice(
                DeleteOnTermination=False,
                VolumeSize=80
            )
        )
    ]
    )
)

ec2_public_instance2 = template.add_resource(
    Instance(
    "EC2PublicInstance2",
    KeyName="polystudent-pair",
    InstanceType="t2.micro",
    ImageId="ami-0eb9fdcf0d07bd5ef",
    AvailabilityZone="ca-central-1b",
    SecurityGroupIds=[Ref(security_group)],
    SubnetId=Ref(public_subnet2),
    IamInstanceProfile="iam-instances",
    BlockDeviceMappings=[
        BlockDeviceMapping(
            DeviceName="/dev/sda1",
            Ebs=EBSBlockDevice(
                DeleteOnTermination=False,
                VolumeSize=80
            )
        )
    ]
    )
)


ec2_private_instance1 = template.add_resource(
    Instance(
    "EC2PrivateInstance1",
    KeyName="polystudent-pair",
    InstanceType="t2.micro",
    ImageId="ami-0eb9fdcf0d07bd5ef",
    AvailabilityZone="ca-central-1a",
    SecurityGroupIds=[Ref(security_group)],
    SubnetId=Ref(private_subnet1),
    IamInstanceProfile="iam-instances",
    BlockDeviceMappings=[
        BlockDeviceMapping(
            DeviceName="/dev/sda1",
            Ebs=EBSBlockDevice(
                DeleteOnTermination=False,
                VolumeSize=80
            )
        )
    ]
    )
)


ec2_private_instance2 = template.add_resource(
    Instance(
    "EC2PrivateInstance2",
    KeyName="polystudent-pair",
    InstanceType="t2.micro",
    ImageId="ami-0eb9fdcf0d07bd5ef",
    AvailabilityZone="ca-central-1b",
    SecurityGroupIds=[Ref(security_group)],
    SubnetId=Ref(private_subnet2),
    IamInstanceProfile="iam-instances",
    BlockDeviceMappings=[
        BlockDeviceMapping(
            DeviceName="/dev/sda1",
            Ebs=EBSBlockDevice(
                DeleteOnTermination=False,
                VolumeSize=80
            )
        )
    ]
    )
)

alarm_sns_topic = template.add_resource(
    Topic(
        "AlarmSNSTopic",
        DisplayName="CloudWatch Alarm Notifications",
        Subscription=[
            Subscription(
                Protocol="email",
                Endpoint="charles-thibault.sanchez@polymtl.ca"  
            )
        ]
    )
)

cloudwatch_alarm = template.add_resource(
    cloudwatch.Alarm(
        "IngressPacketsAlarm",
        AlarmDescription="Alarm for average ingress packets exceeding 1000 pkts/sec",
        MetricName="NetworkIn",  # Metric for ingress traffic
        Namespace="AWS/EC2",
        Statistic="Average",
        Period=60,  # Period in seconds (1 minute)
        EvaluationPeriods=1,  # Trigger alarm if the threshold is breached for 1 period
        Threshold=1000,  # 1000 packets per second
        ComparisonOperator="GreaterThanOrEqualToThreshold",
        Dimensions=[
            cloudwatch.MetricDimension(
                Name="InstanceId",
                Value="*"  # Apply to all instances
            )
        ],
        AlarmActions=[
            Ref(alarm_sns_topic)  # Replace with an SNS Topic to notify
        ],
        OKActions=[
            Ref(alarm_sns_topic)  # Notify when alarm returns to OK
        ]
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
"""
template.add_output(
    Output(
        "VPCFlowLogId",
        Description="ID of the VPC Flow Log",
        Value=Ref(vpc_flow_log)
    )
)
"""
template.add_output(
    Output(
        "EC2PublicInstance1Id",
        Description="ID of the EC2 instance",
        Value=Ref(ec2_public_instance1)
    )
)

template.add_output(
    Output(
        "EC2PublicInstance2Id",
        Description="ID of the EC2 instance",
        Value=Ref(ec2_public_instance2)
    )
)

template.add_output(
    Output(
        "EC2PrivateInstance1Id",
        Description="ID of the EC2 instance",
        Value=Ref(ec2_private_instance1)
    )
)

template.add_output(
    Output(
        "EC2PrivateInstance2Id",
        Description="ID of the EC2 instance",
        Value=Ref(ec2_private_instance2)
    )
)


############ boto3 ############

with open('cloudwatch.yml', 'w') as f:
    f.write(template.to_yaml())

print("Template yml bien généré dans le fichier")


with open('cloudwatch.yml', 'r') as template:
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
