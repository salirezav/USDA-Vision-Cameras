# AI Agent Resources

This directory contains resources specifically designed to help AI agents understand and work with the USDA Vision Camera System.

## Directory Structure

### `/guides/`
Contains comprehensive guides for AI agents:
- `AI_AGENT_INSTRUCTIONS.md` - Specific instructions for AI agents working with this system
- `AI_INTEGRATION_GUIDE.md` - Guide for integrating AI capabilities with the camera system

### `/examples/`
Contains practical examples and demonstrations:
- `demos/` - Python demo scripts showing various system capabilities
- `notebooks/` - Jupyter notebooks with interactive examples and tests

### `/references/`
Contains API references and technical specifications:
- `api-endpoints.http` - HTTP API endpoint examples
- `api-tests.http` - API testing examples
- `streaming-api.http` - Streaming API examples
- `camera-api.types.ts` - TypeScript type definitions for the camera API

## Key Learning Resources

1. **System Architecture**: Review the main system structure in `/usda_vision_system/`
2. **Configuration**: Study `config.json` for system configuration options
3. **API Documentation**: Check `/docs/api/` for API specifications
4. **Feature Guides**: Review `/docs/features/` for feature-specific documentation
5. **Test Examples**: Examine `/tests/` for comprehensive test coverage

## Quick Start for AI Agents

1. Read `guides/AI_AGENT_INSTRUCTIONS.md` first
2. Review the demo scripts in `examples/demos/`
3. Study the API references in `references/`
4. Examine test files to understand expected behavior
5. Check configuration options in the root `config.json`

## System Overview

The USDA Vision Camera System is a multi-camera monitoring and recording system with:
- Real-time camera streaming
- MQTT-based automation
- Auto-recording capabilities
- RESTful API interface
- Web-based camera preview
- Comprehensive logging and monitoring

For detailed system documentation, see the `/docs/` directory.
