#!/usr/bin/env bash
set -euo pipefail

STACK_NAME="ArbeeResources"
TEMPLATE_FILE="./ops/deployments/cloudformation.yml"
DB_USER="$DB_USER"
DB_PASSWORD="$DB_PASS"
DB_NAME="$DB_NAME"

# Selects default VPC
VPC_ID=$(aws ec2 describe-vpcs \
  --filters Name=isDefault,Values=true \
  --query 'Vpcs[0].VpcId' \
  --output text)

# Always selects the default subnet in AZ: ap-southeast-2a
AZ="ap-southeast-2a"
SUBNET_ID=$(
  aws ec2 describe-subnets \
    --filters \
    Name=vpc-id,Values=${VPC_ID} \
    Name=default-for-az,Values=true \
    Name=availability-zone,Values=${AZ} \
    --query 'Subnets[0].SubnetId' \
    --output text
)

echo "Deploying into VPC ${VPC_ID}, Subnet ${SUBNET_ID}…"
aws cloudformation deploy \
  --stack-name "$STACK_NAME" \
  --template-file "$TEMPLATE_FILE" \
  --parameter-overrides \
  DBName="$DB_NAME" \
  DBUser="$DB_USER" \
  DBPassword="$DB_PASSWORD" \
  VpcId="$VPC_ID" \
  SubnetId="$SUBNET_ID" \
  --capabilities CAPABILITY_NAMED_IAM

# Check if the stack was deployed successfully
if [ $? -eq 0 ]; then
  echo "CloudFormation stack deployed successfully."
else
  echo "Failed to deploy CloudFormation stack."
  exit 1
fi
