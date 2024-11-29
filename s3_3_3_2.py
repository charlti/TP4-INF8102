import boto3
from troposphere import Template, Output, Ref, Join
from troposphere.s3 import (
    Bucket, 
    BucketPolicy,
    PublicAccessBlockConfiguration, 
    BucketEncryption, 
    ServerSideEncryptionRule, 
    ServerSideEncryptionByDefault, 
    VersioningConfiguration,
)
from troposphere.cloudtrail import Trail, DataResource, EventSelector

def create_s3_template():
    template = Template()
    template.set_description("S3 bucket with replication and CloudTrail logging")

    # Création de la configuration du blocage d'accès public
    public_access_block = PublicAccessBlockConfiguration(
        BlockPublicAcls=True,
        BlockPublicPolicy=True,
        IgnorePublicAcls=True,
        RestrictPublicBuckets=True
    )

    # Configuration du chiffrement
    encryption = BucketEncryption(
        ServerSideEncryptionConfiguration=[
            ServerSideEncryptionRule(
                ServerSideEncryptionByDefault=ServerSideEncryptionByDefault(
                    SSEAlgorithm="aws:kms",
                    KMSMasterKeyID="arn:aws:kms:ca-central-1:123994170748:key/21987f29-4a5c-494c-a0c0-62191770439b"
                )
            )
        ]
    )

    # Configuration du versioning
    versioning = VersioningConfiguration(
        Status="Enabled"
    )

    # Création des buckets
    source_bucket = template.add_resource(Bucket(
        "S3Bucket",
        BucketName="polystudentsbucket",
        AccessControl="Private",
        PublicAccessBlockConfiguration=public_access_block,
        BucketEncryption=encryption,
        VersioningConfiguration=versioning
    ))

    destination_bucket = template.add_resource(Bucket(
        "ReplicaBucket",
        BucketName="polystudentsbucket-back",
        AccessControl="Private",
        PublicAccessBlockConfiguration=public_access_block,
        BucketEncryption=encryption,
        VersioningConfiguration=versioning
    ))

    # Configuration de la politique du bucket pour CloudTrail
    source_bucket_policy = template.add_resource(BucketPolicy(
        "S3BucketPolicy",
        Bucket=Ref(source_bucket),
        PolicyDocument={
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AWSCloudTrailAclCheck20150319",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "cloudtrail.amazonaws.com"
                    },
                    "Action": [
                        "s3:GetBucketAcl",
                        "s3:ListBucket"
                    ],
                    "Resource": Join("", ["arn:aws:s3:::", Ref(source_bucket)])
                },
                {
                    "Sid": "AWSCloudTrailWrite20150319",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "cloudtrail.amazonaws.com"
                    },
                    "Action": "s3:PutObject",
                    "Resource": Join("", ["arn:aws:s3:::", Ref(source_bucket), "/AWSLogs/*"]),
                    "Condition": {
                        "StringEquals": {
                            "s3:x-amz-acl": "bucket-owner-full-control"
                        }
                    }
                }
            ]
        }
    ))

    # Enable CloudTrail to log S3 data events
    cloudtrail = template.add_resource(Trail(
        "CloudTrail",
        TrailName="S3ActivityTrail",
        S3BucketName=Ref(source_bucket),
        IsLogging=True,
        IsMultiRegionTrail=True,
        IncludeGlobalServiceEvents=True,
        EventSelectors=[
            EventSelector(
                ReadWriteType="All",
                IncludeManagementEvents=True,
                DataResources=[
                    DataResource(
                        Type="AWS::S3::Object",
                        Values=[
                            Join("", ["arn:aws:s3:::", Ref(source_bucket), "/"]),
                        ]
                    )
                ]
            )
        ]
    ))

    # Ajout des outputs
    template.add_output([
        Output(
            "SourceBucketName",
            Description="Source Bucket Created! ;)",
            Value=Ref(source_bucket)
        ),
        Output(
            "CloudTrailName",
            Description="CloudTrail Name for S3 Activity Logging",
            Value=Ref(cloudtrail)
        )
    ])

    return template


def deploy_template():
    access_key = 'your_access_key'
    secret_key = 'your_secret_key'
    region = 'your_region'

    cf_client = boto3.client('cloudformation', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)
    
    template = create_s3_template()
    
    # Déployer le stack
    stack_name = "s3-replication-with-cloudtrail-stack"
    cf_client.create_stack(
        StackName=stack_name,
        TemplateBody=template.to_json(),
        Capabilities=["CAPABILITY_IAM"]
    )

    print(f"Déploiement du stack {stack_name} en cours...")

if __name__ == "__main__":
    deploy_template()