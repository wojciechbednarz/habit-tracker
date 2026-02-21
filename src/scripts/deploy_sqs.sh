#!/bin/bash

# Important: This script must be run from the repository root directory. Also, ensure that AWS CLI and SAM CLI are installed and configured.

# Load environment variables from .env (if exists)

# Get the .env file and source it to load environment variables
SCRIPT_DIR="$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)"
ENV_FILE="$SCRIPT_DIR/../../.env"
set -a
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
else
    echo "Error: .env file not found at $ENV_FILE"
    exit 1
fi
set +a

# Configuration
STACK_NAME=$AWS_SQS_STACK_NAME
TEMPLATE_FILE="./src/infrastructure/aws/data/sqs_queue.yml"
REGION=$AWS_REGION # Change as needed

echo "--- Deploying SQS Stack: $STACK_NAME ---"

# Step 1: Validate template (runs from repo root)
echo "Validating template..."
sam.cmd validate -t $TEMPLATE_FILE

if [ $? -ne 0 ]; then
    echo "Template validation failed!"
    exit 1
fi

# Step 2: Deploy
echo "Deploying stack..."
sam.cmd deploy \
    --template-file $TEMPLATE_FILE \
    --stack-name $STACK_NAME \
    --region $REGION \
    --capabilities CAPABILITY_IAM \
    --no-confirm-changeset \
    --no-fail-on-empty-changeset

if [ $? -eq 0 ]; then
    echo "Successfully deployed!"

    echo "--- Stack Outputs ---"
    aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query 'Stacks[0].Outputs' \
        --output table
else
    echo "Deployment failed!"
    exit 1
fi
