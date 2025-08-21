#!/bin/bash

# Ninode Service Installer
set -e

API_KEY="$1"
NINODE_DIR="/opt/ninode"
SERVICE_NAME="ninode"
DOWNLOAD_URL="https://raw.githubusercontent.com/michaelsieminski/ninode-service/main"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
fi

# Validate API key
if [ -z "$API_KEY" ]; then
    print_error "Usage: curl -sSL https://app.ninode.com/install.sh | bash -s -- YOUR_API_KEY"
fi

print_status "Installing Ninode Service..."

# Detect architecture
ARCH=$(uname -m)
case $ARCH in
    x86_64)
        ARCH="amd64"
        ;;
    aarch64)
        ARCH="arm64"
        ;;
    *)
        print_error "Unsupported architecture: $ARCH"
        ;;
esac

# Detect OS
OS=$(uname -s | tr '[:upper:]' '[:lower:]')

# Create directory
print_status "Creating installation directory..."
mkdir -p $NINODE_DIR
cd $NINODE_DIR

# Download ninode-service binary
BINARY_NAME="ninode-service-${OS}-${ARCH}"
print_status "Downloading Ninode service binary..."

curl -sSL "${DOWNLOAD_URL}/ninode-service.py" -o ninode-service.py
chmod +x ninode-service.py

# Download MCP server
print_status "Downloading MCP server..."
curl -sSL "${DOWNLOAD_URL}/mcp_server.py" -o mcp_server.py
chmod +x mcp_server.py

# Check for python3 and install if needed
if ! command -v python3 &> /dev/null; then
    print_status "Installing Python3..."
    if command -v apt-get &> /dev/null; then
        apt-get update && apt-get install -y python3 python3-pip
    elif command -v yum &> /dev/null; then
        yum install -y python3 python3-pip
    elif command -v dnf &> /dev/null; then
        dnf install -y python3 python3-pip
    elif command -v apk &> /dev/null; then
        apk add python3 py3-pip py3-virtualenv
    elif command -v pacman &> /dev/null; then
        pacman -S --noconfirm python python-pip python-virtualenv
    else
        print_error "Could not install Python3. Please install manually."
    fi
fi

# Install the version-specific venv package for Debian/Ubuntu systems
if command -v apt-get &> /dev/null; then
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    print_status "Installing Python venv package..."
    apt-get install -y python${PYTHON_VERSION}-venv
fi

print_status "Creating Python virtual environment..."
python3 -m venv $NINODE_DIR/venv

print_status "Installing Python dependencies..."
$NINODE_DIR/venv/bin/pip install fastapi uvicorn psutil httpx pydantic mcp

# Create config file
print_status "Creating configuration..."
cat > config.json << EOF
{
    "api_key": "$API_KEY",
    "server_url": "https://app.ninode.com",
    "port": 6969,
    "host": "0.0.0.0",
    "update_interval_hours": 24,
    "enable_auto_update": true
}
EOF

# Create systemd service
print_status "Creating systemd service..."
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Ninode Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$NINODE_DIR
ExecStart=$NINODE_DIR/venv/bin/python $NINODE_DIR/ninode-service.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
print_status "Starting Ninode service..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME

# Create MCP configuration for users
print_status "Setting up MCP server configuration..."
MCP_CONFIG_TEMPLATE="/opt/ninode/mcp-config-template.json"
cat > $MCP_CONFIG_TEMPLATE << EOF
{
  "mcpServers": {
    "ninode": {
      "command": "$NINODE_DIR/venv/bin/python",
      "args": ["$NINODE_DIR/mcp_server.py"],
      "env": {}
    }
  }
}
EOF

# Check if service is running
sleep 2
if systemctl is-active --quiet $SERVICE_NAME; then
    print_status "✅ Ninode service installed and running successfully!"
    print_status "Service status: $(systemctl is-active $SERVICE_NAME)"
    print_status "Port: 6969"
    
    # Test connection to web app
    print_status "Testing connection to Ninode servers..."
    if curl -sSf "https://app.ninode.com/api/v1/status" -H "Authorization: Bearer $API_KEY" > /dev/null; then
        print_status "✅ Successfully connected to Ninode servers!"
    else
        print_warning "⚠️  Could not connect to Ninode servers. Please check your API key."
    fi
else
    print_error "❌ Failed to start Ninode service. Check logs with: journalctl -u $SERVICE_NAME"
fi

print_status "Installation complete!"
print_status ""
print_status "Logs: journalctl -u $SERVICE_NAME -f"
print_status "Stop: systemctl stop $SERVICE_NAME"
print_status "Restart: systemctl restart $SERVICE_NAME"