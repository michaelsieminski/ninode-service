# Ninode Service

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Python](https://img.shields.io/badge/python-3.12+-blue.svg) ![FastAPI](https://img.shields.io/badge/FastAPI-0.116+-green.svg)

**Ninode Service** is the connector service that runs on your VPS servers when using Ninode. It acts as an intelligent bridge between the Ninode Web App and your server infrastructure, providing automated server management, monitoring, and maintenance through natural language interactions.

## What is Ninode?

Ninode is your AI-powered system administrator that connects to your VPS and manages it through simple chat. Set up services, secure your server, deploy apps, and automate tasks with ease. Add monitors and let Ninode proactively fix issues - all without touching the command line.

## Features

- **AI-Powered Management**: Communicate with your server using natural language
- **Secure Communication**: End-to-end encrypted communication with the Ninode Web App
- **Real-time Monitoring**: Proactive system monitoring and issue detection
- **Service Management**: Automated deployment, configuration, and maintenance
- **MCP Server**: Provides Model Context Protocol server for AI interactions
- **Resource Tracking**: Monitor CPU, memory, disk usage, and performance metrics
- **Alert System**: Intelligent alerting and automated issue resolution
- **Multi-Platform**: Supports major Linux distributions
- **Open Source**: Fully transparent - no hidden backdoors or secret functionality

## Development

### Setup Development Environment

```bash
# Clone and enter directory
git clone https://github.com/michaelsieminski/ninode-service.git
cd ninode-service

# Install with development dependencies
uv sync --dev

# Or with pip
pip install -e ".[dev]"
```

### Code Quality

We use Ruff for linting and formatting:

```bash
# Format code
uv run ruff format

# Lint code
uv run ruff check

# Fix linting issues
uv run ruff check --fix
```

### Testing

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=ninode_service
```

## Contributing

We welcome contributions! This project is open source to ensure transparency and community involvement.

### Development Guidelines

- Follow the existing code style and conventions
- Write tests for new features and bug fixes
- Update documentation for any API changes
- Ensure all CI checks pass
- Be respectful and constructive in discussions

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
