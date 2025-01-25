#!/bin/bash

# Configuration
S3_BUCKET="sd3-kserve"
MODEL_DIR="sd3-model"
CONFIG_DIR="./config"
MAR_FILE="./model-store/sd3.mar"

# Upload model files to S3
echo "Uploading model files to S3..."
aws s3 cp --recursive ${MODEL_DIR} s3://${S3_BUCKET}/sd3/sd3-model/

# Upload config file to S3
echo "Uploading config file to S3..."
aws s3 cp ${CONFIG_DIR}/config.properties s3://${S3_BUCKET}/sd3/config/

# Upload MAR file if it exists
echo "Uploading MAR file to S3..."
aws s3 cp ${MAR_FILE} s3://${S3_BUCKET}/sd3/model-store/

echo "Upload complete!"