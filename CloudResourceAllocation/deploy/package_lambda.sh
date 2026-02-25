#!/bin/bash
# Script to package Lambda functions for deployment

set -e

PROJECT_DIR="/Users/apple/Desktop/cv_project"
PACKAGE_DIR="$PROJECT_DIR/lambda_packages"

echo "=== Packaging Lambda Functions ==="

# Clean previous packages
rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR"

# Package Lambda 1: Submission Handler
echo "Packaging submission_handler..."
mkdir -p "$PACKAGE_DIR/submission_handler"
cp "$PROJECT_DIR/lambda/submission_handler.py" "$PACKAGE_DIR/submission_handler/"

cd "$PACKAGE_DIR/submission_handler"
# Install boto3 (Lambda runtime includes it, but we include it for safety)
pip3 install boto3 -t . --quiet
zip -r ../submission_handler.zip . > /dev/null
cd "$PROJECT_DIR"
echo "✓ Created: lambda_packages/submission_handler.zip"

# Package Lambda 2: Get and Send
echo "Packaging get_and_send..."
mkdir -p "$PACKAGE_DIR/get_and_send"
cp "$PROJECT_DIR/lambda/get_and_send.py" "$PACKAGE_DIR/get_and_send/"

cd "$PACKAGE_DIR/get_and_send"
# Install boto3 and requests
pip3 install boto3 requests -t . --quiet
zip -r ../get_and_send.zip . > /dev/null
cd "$PROJECT_DIR"
echo "✓ Created: lambda_packages/get_and_send.zip"

echo ""
echo "=== Packaging Complete ==="
echo "Lambda packages are ready in: $PACKAGE_DIR"
echo ""
echo "Files created:"
ls -lh "$PACKAGE_DIR"/*.zip
echo ""
echo "Next steps:"
echo "1. Go to AWS Lambda Console"
echo "2. Create function 'submission-handler'"
echo "3. Upload: lambda_packages/submission_handler.zip"
echo "4. Create function 'get-and-send'"
echo "5. Upload: lambda_packages/get_and_send.zip"

