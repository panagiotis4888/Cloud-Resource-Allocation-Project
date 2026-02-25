#!/bin/bash
# Minimal Lambda packaging (boto3 is included in Lambda runtime)
# Only packages the Python code - dependencies like boto3 and requests 
# should be added manually if needed, or use Lambda layers

set -e

PROJECT_DIR="/Users/apple/Desktop/cv_project"
PACKAGE_DIR="$PROJECT_DIR/lambda_packages"

echo "=== Packaging Lambda Functions (Minimal) ==="

# Clean previous packages
rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR"

# Package Lambda 1: Submission Handler
# Note: boto3 is included in Lambda runtime, no need to package
echo "Packaging submission_handler..."
mkdir -p "$PACKAGE_DIR/submission_handler"
cp "$PROJECT_DIR/lambda/submission_handler.py" "$PACKAGE_DIR/submission_handler/"

cd "$PACKAGE_DIR/submission_handler"
zip -r ../submission_handler.zip . > /dev/null
cd "$PROJECT_DIR"
echo "✓ Created: lambda_packages/submission_handler.zip ($(ls -lh lambda_packages/submission_handler.zip | awk '{print $5}'))"

# Package Lambda 2: Get and Send
# Note: boto3 is included in Lambda runtime
# requests library will need to be added via Lambda Layer or included manually
echo "Packaging get_and_send..."
mkdir -p "$PACKAGE_DIR/get_and_send"
cp "$PROJECT_DIR/lambda/get_and_send.py" "$PACKAGE_DIR/get_and_send/"

cd "$PACKAGE_DIR/get_and_send"
zip -r ../get_and_send.zip . > /dev/null
cd "$PROJECT_DIR"
echo "✓ Created: lambda_packages/get_and_send.zip ($(ls -lh lambda_packages/get_and_send.zip | awk '{print $5}'))"

echo ""
echo "=== Packaging Complete ==="
echo "Lambda packages are ready in: $PACKAGE_DIR"
echo ""
echo "Files created:"
ls -lh "$PACKAGE_DIR"/*.zip
echo ""
echo "IMPORTANT NOTES:"
echo "1. boto3 is included in Lambda runtime - no need to package it"
echo "2. For get_and_send.zip, you may need to add 'requests' library:"
echo "   Option A: Use AWS Lambda Layer for requests (recommended)"
echo "   Option B: Manually install requests and package it later"
echo ""
echo "Next steps:"
echo "1. Go to AWS Lambda Console"
echo "2. Create function 'submission-handler'"
echo "3. Upload: lambda_packages/submission_handler.zip"
echo "4. Create function 'get-and-send'"
echo "5. Upload: lambda_packages/get_and_send.zip"
echo "6. For get-and-send, add AWS Lambda Layer for requests (or package manually)"

