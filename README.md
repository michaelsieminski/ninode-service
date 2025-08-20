# Ninode Service

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Python](https://img.shields.io/badge/python-3.8+-blue.svg) ![FastAPI](https://img.shields.io/badge/FastAPI-latest-green.svg)

**Ninode Service** is a lightweight FastAPI-based agent that runs on your VPS servers, enabling secure communication with the Ninode web application for automated server management and monitoring.

## What is Ninode?

Ninode is your AI-powered system administrator that connects to your VPS and manages it through simple chat. Set up services, secure your server, deploy apps, and automate tasks with ease.

## Installation

Install on your VPS with a single command:

```bash
curl -sSL https://app.ninode.com/install.sh | bash -s -- YOUR_API_KEY
```

## Features

- **Lightweight**: Single Python file, minimal dependencies
- **Secure**: Bearer token authentication, command whitelist
- **Automatic Registration**: Registers with Ninode web app on startup
- **System Monitoring**: CPU, memory, disk metrics
- **Safe Command Execution**: Only allows read-only system commands
- **Multi-Platform**: Supports major Linux distributions

## API Endpoints

- `GET /health` - Health check (no auth)
- `GET /status` - System status (auth required)
- `GET /metrics` - System metrics (auth required)
- `POST /execute` - Execute whitelisted commands (auth required)

## Configuration

Service reads configuration from `/opt/ninode/config.json`:

```json
{
  "api_key": "your-api-key-here",
  "server_url": "https://app.ninode.com",
  "port": 6969,
  "host": "0.0.0.0"
}
```

## Development

```bash
# Clone repository
git clone https://github.com/michaelsieminski/ninode-service.git
cd ninode-service

# Run service locally (requires config.json)
python3 ninode-service.py

# Format code
ruff format ninode-service.py

# Lint code
ruff check ninode-service.py
```

## License

MIT License - see [LICENSE](LICENSE) file for details.
