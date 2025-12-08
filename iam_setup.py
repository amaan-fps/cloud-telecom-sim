import json
import boto3
iam = boto3.client('iam')

role_name = "TelecomCloudWatchRole"
profile_name = "TelecomCollectorProfile"

# create instance profile (if missing) and add role
try:
    iam.create_instance_profile(InstanceProfileName=profile_name)
except Exception:
    pass

try:
    iam.add_role_to_instance_profile(InstanceProfileName=profile_name, RoleName=role_name)
except Exception as e:
    print("add_role_to_instance_profile:", e)
