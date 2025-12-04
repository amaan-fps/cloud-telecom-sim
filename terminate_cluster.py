import boto3

REGION = "ap-south-1"
PROJECT_TAG = "CloudTelecomSim"

ec2 = boto3.resource("ec2", region_name=REGION)

instances = ec2.instances.filter(
    Filters=[{"Name": "tag:Project", "Values": [PROJECT_TAG]}]
)

ids = [i.id for i in instances]

if ids:
    print("Terminating instances:", ids)
    ec2.instances.filter(InstanceIds=ids).terminate()
else:
    print("No instances found for this project.")
