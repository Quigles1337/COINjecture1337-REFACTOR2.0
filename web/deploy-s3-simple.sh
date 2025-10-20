#!/usr/bin/env bash
set -euo pipefail

BUCKET_NAME="coinjecture.com"
REGION="us-east-1"

echo "Creating bucket (if not exists)"
aws s3api create-bucket --bucket "$BUCKET_NAME" --region "$REGION" || true

echo "Enable website hosting"
aws s3 website s3://"$BUCKET_NAME"/ --index-document index.html --error-document index.html

echo "Sync web/ to bucket"
aws s3 sync . s3://"$BUCKET_NAME"/ --delete

echo "Done. Website endpoint is listed in the S3 console for bucket $BUCKET_NAME"
