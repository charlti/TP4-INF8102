import boto3
from troposphere import Template, Output, Ref
from troposphere.s3 import Bucket, PublicAccessBlockConfiguration, BucketEncryption, ServerSideEncryptionRule, ServerSideEncryptionByDefault, VersioningConfiguration

def create_s3_template():
    template = Template()
    template.set_description("S3 bucket")

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

    # Création du bucket
    bucket = template.add_resource(Bucket(
        "S3Bucket",
        BucketName="polystudentsbucket",
        AccessControl="Private",
        PublicAccessBlockConfiguration=public_access_block,
        BucketEncryption=encryption,
        VersioningConfiguration=versioning
    ))

    # Ajout de l'output
    template.add_output(Output(
        "S3Bucket",
        Description="Bucket Created! ;)",
        Value=Ref(bucket)
    ))

    return template


def deploy_template():
    import boto3

    access_key = 'your_access_key'
    secret_key = 'your_secret_key'
    region = 'your_region'

    cf_client = boto3.client('cloudformation', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)
    
    template = create_s3_template()
    
    # Initialiser le client CloudFormation
    
    # Déployer le stack
    stack_name = "s3-secure-bucket-stack"
    cf_client.create_stack(
        StackName=stack_name,
        TemplateBody=template.to_json(),
    )

    print(f"Déploiement du stack {stack_name} en cours...")

if __name__ == "__main__":
    deploy_template()
