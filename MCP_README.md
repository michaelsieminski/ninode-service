# Ninode MCP Server

An MCP (Model Context Protocol) server that provides AI agents with tools to interact with ninode-service instances for VPS monitoring and management.

## Features

The MCP server provides the following tools for AI agents:

### 🔧 Server Management
- `ninode_configure_server` - Add or update server configurations
- `ninode_list_servers` - List all configured servers
- `ninode_health_check` - Check if a server is healthy and responding

### 📊 System Monitoring
- `ninode_get_status` - Get detailed system status and information
- `ninode_get_metrics` - Get comprehensive system metrics (CPU, memory, disk, load)

### ⚡ Command Execution
- `ninode_execute_command` - Execute system commands on remote servers
- `ninode_trigger_update` - Trigger manual service updates

## Installation

### Option 1: Automatic Installation
Run the provided installation script:
```bash
sudo ./install.sh
```

### Option 2: Manual Installation

1. **Install dependencies**:
```bash
pip3 install fastapi uvicorn httpx pydantic mcp
```

2. **Copy files to installation directory**:
```bash
sudo mkdir -p /opt/ninode
sudo cp mcp_server.py /opt/ninode/
sudo chmod +x /opt/ninode/mcp_server.py
```

3. **Configure MCP in Claude Code**:
Add to your Claude Code MCP configuration file (`~/.config/mcp/settings.json`):
```json
{
  "mcpServers": {
    "ninode": {
      "command": "python3",
      "args": ["/opt/ninode/mcp_server.py"],
      "env": {}
    }
  }
}
```

## Usage

### 1. Configure a Ninode Server

First, add a ninode-service instance to the MCP server:

```
ninode_configure_server:
- name: "my-vps"
- url: "http://your-vps-ip:6969" 
- api_key: "your-api-key-here"
```

### 2. Check Server Health

Verify the server is responding:

```
ninode_health_check:
- server_name: "my-vps"
```

### 3. Get System Status

Retrieve basic system information:

```
ninode_get_status:
- server_name: "my-vps"
```

### 4. Get System Metrics

Get detailed system metrics:

```
ninode_get_metrics:
- server_name: "my-vps"
```

### 5. Execute Commands

Run system commands (from the allowed list):

```
ninode_execute_command:
- server_name: "my-vps"
- command: "df"
- args: ["-h"]
```

### 6. Trigger Updates

Check for and apply service updates:

```
ninode_trigger_update:
- server_name: "my-vps"
```

## Available Commands

The ninode-service allows execution of these system commands:
- `ps` - Show running processes
- `df` - Show disk usage
- `free` - Show memory usage  
- `uptime` - Show system uptime
- `whoami` - Show current user
- `uname` - Show system information
- `hostname` - Show hostname
- `date` - Show current date/time
- `id` - Show user ID information
- `w` - Show logged in users
- `who` - Show who is logged on
- `last` - Show last logins
- `lscpu` - Show CPU information
- `lsblk` - Show block devices
- `mount` - Show mounted filesystems

## Configuration

### Server Configuration Format

Each ninode server requires:
- `name`: Unique identifier for the server
- `url`: Base URL of the ninode-service (e.g., `http://192.168.1.100:6969`)
- `api_key`: Authentication token for the ninode-service
- `timeout`: (Optional) Request timeout in seconds (default: 30)

### Example AI Prompts

Here are example prompts you can use with an AI agent that has access to this MCP server:

**"Check the status of my VPS"**
The AI will use `ninode_get_status` to retrieve system information.

**"Show me the disk usage on my server"**
The AI will use `ninode_execute_command` with the `df -h` command.

**"Get detailed system metrics"**
The AI will use `ninode_get_metrics` to show memory, disk, and load information.

**"Update my ninode service"**
The AI will use `ninode_trigger_update` to check for and apply updates.

## Security Considerations

- The MCP server communicates with ninode-service instances over HTTP/HTTPS
- Authentication is handled via Bearer tokens (API keys)
- Only predefined system commands can be executed
- All commands are logged by the ninode-service

## Troubleshooting

### Common Issues

1. **"Server not configured" error**
   - Use `ninode_configure_server` to add your server first

2. **Connection timeout**
   - Check that the ninode-service is running on the target server
   - Verify the URL and port are correct
   - Check firewall settings

3. **Authentication failed**
   - Verify the API key is correct
   - Check that the API key matches the ninode-service configuration

4. **MCP server not starting**
   - Ensure all Python dependencies are installed
   - Check that the MCP server path is correct in your configuration

### Debugging

Enable debug logging by setting the `DEBUG` environment variable:

```bash
DEBUG=1 python3 /opt/ninode/mcp_server.py
```

## Integration Example

Here's how the MCP server integrates with your workflow:

1. **Web App AI** calls MCP tools through Claude Code
2. **MCP Server** receives tool calls and makes HTTP requests
3. **Ninode Service** on your VPS executes commands and returns results
4. **MCP Server** formats and returns results to the AI
5. **Web App AI** presents information to the user

```
Web App AI → Claude Code → MCP Server → Ninode Service → VPS
                   ↑                              ↓
                Results ← Formatted ← Response ← Commands
```

This creates a seamless bridge between your AI applications and server management tasks.