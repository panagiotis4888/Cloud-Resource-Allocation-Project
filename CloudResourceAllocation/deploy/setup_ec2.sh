#!/bin/bash
# EC2 Setup Script for User and Provider instances
# Usage: ./setup_ec2.sh [user|provider] [S1|S2|S3]

set -e

ROLE=$1  # "user" or "provider"
USER_ID=$2  # For user instances: "S1", "S2", or "S3"

echo "========================================="
echo "EC2 Setup Script"
echo "Role: $ROLE"
if [ "$ROLE" = "user" ]; then
    echo "User ID: $USER_ID"
fi
echo "========================================="

# Update system
echo "Updating system packages..."
sudo yum update -y || sudo apt-get update -y

# Install Python 3.9+ if not present
echo "Installing Python..."
if command -v python3 &>/dev/null; then
    echo "Python3 already installed: $(python3 --version)"
else
    sudo yum install python3 python3-pip -y || sudo apt-get install python3 python3-pip -y
fi

# Install pip if not present
if ! command -v pip3 &>/dev/null; then
    echo "Installing pip..."
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python3 get-pip.py
    rm get-pip.py
fi

# Create application directory
APP_DIR="/home/ec2-user/app"
if [ -d "$APP_DIR" ]; then
    echo "Removing existing app directory..."
    rm -rf "$APP_DIR"
fi

echo "Creating application directory..."
mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Install Python dependencies
echo "Installing Python dependencies..."
cat > requirements.txt << EOF
Flask==3.0.0
boto3==1.34.0
requests==2.31.0
numpy==1.24.0
EOF

pip3 install -r requirements.txt

echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Copy your application code to: $APP_DIR"
echo "2. Set environment variables (USER_ID, PORT, etc.)"
echo "3. Start the Flask application"
echo ""
echo "To start the application:"
if [ "$ROLE" = "user" ]; then
    echo "  export USER_ID=$USER_ID"
    echo "  export PORT=5000"
    echo "  cd $APP_DIR"
    echo "  nohup python3 user/user_app.py > user.log 2>&1 &"
elif [ "$ROLE" = "provider" ]; then
    echo "  export PORT=5001"
    echo "  cd $APP_DIR"
    echo "  nohup python3 provider/provider_app.py > provider.log 2>&1 &"
fi
echo ""

