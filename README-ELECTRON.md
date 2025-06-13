# Curriculum Curator - Electron Desktop App

This directory contains the Electron desktop application for Curriculum Curator, which provides a modern GUI interface for the curriculum curation workflows.

## Architecture

The Electron app consists of three main components:

1. **Python Backend** - FastAPI server that wraps the existing CLI functionality
2. **React Frontend** - Modern web interface for managing workflows and content
3. **Electron Shell** - Desktop wrapper that bundles everything together

## Development Setup

### Prerequisites

- Python 3.9+
- Node.js 16+
- npm or yarn

### Quick Start

1. **Install Python dependencies** (including web dependencies):
   ```bash
   pip install -e ".[web]"
   ```

2. **Run the development environment**:
   ```bash
   python run-dev.py
   ```

This will start:
- React development server (http://localhost:3000)
- Python API server (http://localhost:8000)
- Electron app (opens automatically)

### Manual Development Setup

If you prefer to run components separately:

1. **Start the Python API server**:
   ```bash
   uvicorn curriculum_curator.web.api:app --host 127.0.0.1 --port 8000 --reload
   ```

2. **Start the React development server**:
   ```bash
   cd web
   npm install
   npm start
   ```

3. **Start Electron** (in another terminal):
   ```bash
   cd electron
   npm install
   npm run electron-dev
   ```

## Building for Production

### Build Everything

Use the provided build script:

```bash
python build-electron.py
```

This will:
1. Build the React frontend
2. Set up Electron dependencies
3. Create a Python bundle
4. Build the Electron application for your platform

### Manual Build Steps

1. **Build React frontend**:
   ```bash
   cd web
   npm run build
   ```

2. **Build Electron app**:
   ```bash
   cd electron
   npm run dist
   ```

The built applications will be in `electron/dist/`.

## Features

### Current Features

- **Dashboard** - Overview of workflow sessions and system status
- **Workflows** - Browse and run available workflows with custom variables
- **Sessions** - View workflow execution history and results
- **Prompts** - Manage prompt templates
- **Validators** - View available content validators
- **Remediators** - View available content remediators

### API Endpoints

The Python backend provides REST API endpoints:

- `GET /health` - Health check
- `GET /api/workflows` - List available workflows
- `POST /api/workflows/run` - Run a workflow
- `GET /api/workflows/sessions` - List workflow sessions
- `GET /api/workflows/sessions/{id}` - Get session details
- `GET /api/prompts` - List prompts
- `GET /api/validators` - List validators
- `GET /api/remediators` - List remediators

## Database

The application uses SQLite for local data persistence:

- **workflow_sessions** - Stores workflow execution sessions
- **prompt_templates** - Caches prompt templates

The database file is created automatically as `curriculum_curator.db`.

## Configuration

### Environment Variables

- `REACT_APP_API_URL` - API server URL (default: http://localhost:8000)
- `ELECTRON_IS_DEV` - Set to '1' for development mode

### Configuration Files

- `config.yaml` - Main configuration (same as CLI version)
- `web/.env` - React environment variables
- `electron/package.json` - Electron build configuration

## Packaging for Distribution

The build process creates platform-specific packages:

- **Windows**: `.exe` installer and portable app
- **macOS**: `.dmg` disk image and `.app` bundle
- **Linux**: AppImage and various package formats

### Cross-platform Building

To build for different platforms, you can use Docker or run the build on each target platform.

## Troubleshooting

### Common Issues

1. **Python server fails to start**
   - Check that all dependencies are installed: `pip install -e ".[web]"`
   - Verify Python path and virtual environment

2. **React build fails**
   - Clear node_modules: `rm -rf web/node_modules && cd web && npm install`
   - Check Node.js version compatibility

3. **Electron app won't start**
   - Check that Python server is running on port 8000
   - Verify all build outputs exist in expected locations

### Logs

In development mode, logs from all three components are displayed in the terminal. In production, check:

- Electron main process logs in the console
- Python API logs (can be configured via structlog)
- React console logs in the developer tools

## Contributing

When adding new features:

1. **Backend changes** - Add API endpoints in `curriculum_curator/web/api.py`
2. **Frontend changes** - Add React components in `web/src/`
3. **Electron changes** - Modify `electron/main.js` for main process changes

Make sure to test both development and production builds before submitting changes.