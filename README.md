# E*TRADE Local API with MCP Integration

A comprehensive, production-ready integration of the E*TRADE API with Model Context Protocol (MCP) support for Claude Desktop. This project creates a local REST API wrapper around the E*TRADE trading platform, enabling AI-assisted trading strategy analysis and execution.

## Overview

This project provides:
- **FastAPI REST Server**: Modern async API wrapper for E*TRADE
- **E*TRADE OAuth Integration**: Complete OAuth 1.0a authentication flow
- **MCP Server**: Model Context Protocol server for Claude Desktop integration
- **Sandbox & Production**: Separate configurations for testing and live trading
- **Docker Containerization**: Easy deployment and testing
- **Comprehensive Documentation**: Full API reference and setup guides

## Architecture

```
E*TRADE Cloud API
    ↑
    │ (OAuth 1.0a)
    │
pyetrade Library
    ↑
    │
FastAPI REST Server (localhost:8000)
    ↑
    │
MCP Server
    ↑
    │
Claude Desktop
```

## Quick Start

See `docs/quick_start_guide.md` for detailed setup instructions.

### Prerequisites
- Python 3.9+
- E*TRADE sandbox credentials
- Claude Desktop (for MCP features)
- Docker (optional, for containerized deployment)

### Installation

```bash
# Clone repository
git clone <your-repo-url>
cd etrade-local-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Add your E*TRADE credentials to .env
```

### Running the Server

```bash
# FastAPI Server
python -m api.main

# In another terminal, start MCP Server
python -m mcp_server.server
```

## Documentation

- **[Document Index](docs/document_index.md)** - Navigation guide for all documentation
- **[Executive Summary](docs/executive_summary.md)** - Project overview and timeline
- **[Quick Start Guide](docs/quick_start_guide.md)** - Setup instructions (Phase 1)
- **[Implementation Plan](docs/etrade_local_api_mcp_plan.md)** - Full 26-task breakdown
- **[Architecture Patterns](docs/etrade_architecture_patterns.md)** - Design decisions
- **[API Research](docs/etrade_api_research.md)** - Library comparison

## Project Structure

```
etrade-local-api/
├── docs/                          # Planning and reference documentation
├── api/                           # FastAPI application
│   ├── __init__.py
│   ├── config.py                  # Pydantic settings
│   ├── models.py                  # Data models
│   ├── etrade_client.py           # pyetrade wrapper
│   ├── main.py                    # FastAPI app
│   └── routes/                    # API endpoints
├── mcp_server/                    # MCP server for Claude
│   ├── __init__.py
│   └── server.py
├── tests/                         # Unit tests
│   ├── __init__.py
│   ├── test_api.py
│   └── test_mcp.py
├── requirements.txt               # Python dependencies
├── .env.example                   # Configuration template
├── .gitignore
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Development Workflow

1. **Break tasks into small components** (15-30 min each)
2. **Write tests first** (TDD approach)
3. **Test each change** locally
4. **Update documentation** when decisions are made
5. **Push code** when tests pass
6. **Code review** when tasks complete

## Technology Stack

- **FastAPI 0.104+**: Modern async Python web framework
- **pyetrade 2.1.1**: E*TRADE API Python wrapper
- **FastMCP 2.1.0**: Simplest MCP server implementation
- **Pydantic 2.5+**: Type-safe data validation
- **pytest 7.4+**: Testing framework
- **Docker**: Containerization

## E*TRADE API Modules

Currently implemented:
- ✅ **Accounts API**: Account listings, balances, portfolio positions
- 🚧 **Orders API**: Order preview, placement, cancellation (in progress)
- 🚧 **Market API**: Stock quotes, option chains (in progress)
- 🚧 **Alerts API**: Alert management (in progress)

## Security

- OAuth 1.0a with HMAC-SHA1 authentication
- Credentials stored in environment variables
- No tokens exposed to clients
- Session-based token storage
- Auto-renewal of expired tokens

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=api --cov=mcp_server

# Docker testing
docker-compose run test
```

## Deployment

See `docs/HOSTING_SETUP.md` for deployment instructions to Google Cloud Run.

## Contributing

This project follows a structured development workflow:
1. Tasks are broken into small, testable components
2. Each change includes appropriate tests
3. Documentation is updated with design decisions
4. Code is reviewed when tasks complete

## Timeline

- **Phase 1**: Foundation setup (1-2 hours)
- **Phase 2**: FastAPI routes (1 week)
- **Phase 3**: MCP integration (3-4 days)
- **Phase 4**: Integration testing (3-4 days)
- **Phase 5**: Enhancement & polish (1+ week)

**Total**: 8-10 weeks

## License

See LICENSE file for details.

## Support

For questions or issues, refer to the documentation files in `docs/` directory.