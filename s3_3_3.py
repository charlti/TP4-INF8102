import boto3
from troposphere import Template, Output, Ref, GetAtt
from troposphere.s3 import (
    Bucket, 
    PublicAccessBlockConfiguration, 
    BucketEncryption, 
    ServerSideEncryptionRule, 
    ServerSideEncryptionByDefault, 
    VersioningConfiguration, 
    ReplicationConfiguration, 
    ReplicationConfigurationRules,
    ReplicationConfigurationRulesDestination
)
from troposphere.iam import Role, Policy

def create_s3_template():
    template = Template()
    template.set_description("S3 bucket with replication")

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

    # Création du bucket de destination
    destination_bucket = template.add_resource(Bucket(
        "ReplicaBucket",
        BucketName="polystudentsbucket-back",
        AccessControl="Private",
        PublicAccessBlockConfiguration=public_access_block,
        BucketEncryption=encryption,
        VersioningConfiguration=versioning
    ))

    # Création du bucket source
    source_bucket = template.add_resource(Bucket(
        "S3Bucket",
        BucketName="polystudentsbucket",
        AccessControl="Private",
        PublicAccessBlockConfiguration=public_access_block,
        BucketEncryption=encryption,
        VersioningConfiguration=versioning
    ))

    # Rôle IAM pour la réplication
    replication_role = template.add_resource(Role(
        "ReplicationRole",
        AssumeRolePolicyDocument={
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "s3.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        },
        Policies=[
            Policy(
                PolicyName="ReplicationPolicy",
                PolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": [
                                "s3:GetReplicationConfiguration",
                                "s3:ListBucket"
                            ],
                            "Resource": "*"
                        },
                        {
                            "Effect": "Allow",
                            "Action": [
                                "s3:GetObjectVersion",
                                "s3:ReplicateObject",
                                "s3:ReplicateDelete",
                                "s3:ReplicateTags"
                            ],
                            "Resource": "*"
                        },
                        {
                            "Effect": "Allow",
                            "Action": "s3:PutObject",
                            "Resource": "*"
                        }
                    ]
                }
            )
        ]
    ))

    # Configuration de la réplication
    replication_config = ReplicationConfiguration(
        Role=GetAtt(replication_role, "Arn"),
        Rules=[
            ReplicationConfigurationRules(
                Id="ReplicateToBackupBucket",
                Status="Enabled",
                Prefix="",  # Réplication de tous les objets
                Destination=ReplicationConfigurationRulesDestination(
                    Bucket=f"arn:aws:s3:::polystudentsbucket-back"
                )
            )
        ]
    )

    source_bucket.ReplicationConfiguration = replication_config

    # Ajout des outputs
    template.add_output(Output(
        "S3Bucket",
        Description="Source Bucket Created! ;)",
        Value=Ref(source_bucket)
    ))

    template.add_output(Output(
        "S3BucketReplica",
        Description="Replica Bucket Created! ;)",
        Value=Ref(destination_bucket)
    ))

    return template


def deploy_template():
    access_key = 'your_access_key'
    secret_key = 'your_secret_key'
    region = 'your_region'

    cf_client = boto3.client('cloudformation', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)
    
    template = create_s3_template()
    
    # Déployer le stack
    stack_name = "s3-secure-bucket-stack"
    cf_client.create_stack(
        StackName=stack_name,
        TemplateBody=template.to_json(),
        Capabilities=["CAPABILITY_IAM"]
    )

    print(f"Déploiement du stack {stack_name} en cours...")

if __name__ == "__main__":
    deploy_template()