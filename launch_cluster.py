import boto3
import time
import sys
from botocore.exceptions import ClientError

# ---------- CONFIG ----------
REGION = "ap-south-1"
AMI_ID = "ami-087d1c9a513324697"  # Example: ami-0cca134ec43cf708f
INSTANCE_TYPE = "t3.micro"
KEY_NAME = "telecom-project-key"
SECURITY_GROUP_ID = "sg-08a95bdc9288da588"  # telecom-sg
SUBNET_ID = "subnet-0db6f526e79faf876"
NODE_COUNT = 3
PROJECT_TAG = "CloudTelecomSim"

# Paths to userdata relative to where you run this script
COLLECTOR_USERDATA_PATH = "userdata/collector_userdata.sh"
NODE_USERDATA_PATH = "userdata/node_userdata.sh"

ec2 = boto3.resource("ec2", region_name=REGION)
client = boto3.client("ec2", region_name=REGION)

def load_userdata(path):
    with open(path, "r") as f:
        return f.read()

def create_instance(name, userdata_script, role):
    try:
        instances = ec2.create_instances(
            ImageId=AMI_ID,
            InstanceType=INSTANCE_TYPE,
            MinCount=1,
            MaxCount=1,
            KeyName=KEY_NAME,
            NetworkInterfaces=[
                {
                    "DeviceIndex": 0,
                    "SubnetId": SUBNET_ID,
                    "AssociatePublicIpAddress": True,
                    "Groups": [SECURITY_GROUP_ID],
                }
            ],
            UserData=userdata_script,
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {"Key": "Project", "Value": PROJECT_TAG},
                        {"Key": "Name", "Value": name},
                        {"Key": "Role", "Value": role},
                    ],
                }
            ],
        )
    except ClientError as e:
        print("Failed to create instance:", e)
        sys.exit(1)

    instance = instances[0]
    print(f"Creating {role} instance: {instance.id} ...")
    instance.wait_until_running()
    instance.reload()

    # Wait for status checks
    print("Waiting for status checks (this may take ~30s)...")
    waiter = client.get_waiter("instance_status_ok")
    waiter.wait(InstanceIds=[instance.id])
    instance.reload()

    print(f"{role} is running at Public: {instance.public_ip_address}, Private: {instance.private_ip_address}")
    return instance

def main():
    collector_userdata = load_userdata(COLLECTOR_USERDATA_PATH)
    node_userdata_template = load_userdata(NODE_USERDATA_PATH)

    print("Creating Collector Node...")
    collector_instance = create_instance(
        name="collector-node",
        userdata_script=collector_userdata,
        role="Collector"
    )
    collector_private_ip = collector_instance.private_ip_address
    print("Collector Private IP:", collector_private_ip)

    nodes = []
    for i in range(1, NODE_COUNT + 1):
        node_ud = node_userdata_template.replace("<COLLECTOR_PRIVATE_IP>", collector_private_ip)
        instance = create_instance(
            name=f"base-station-{i}",
            userdata_script=node_ud,
            role="BaseStation"
        )
        nodes.append(instance)

    print("\nCluster Launch Complete ✔")
    print("Collector:", collector_instance.public_ip_address)
    for idx, n in enumerate(nodes, 1):
        print(f"Node {idx}: {n.public_ip_address}")

if __name__ == "__main__":
    main()
