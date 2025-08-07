#!/usr/bin/env bash

# Robust Backend Setup and Run Script for Curriculum Curator
# Handles virtual environment, dependencies, and configuration

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VENV_DIR=".venv"
ENV_FILE=".env"
PORT="${PORT:-8000}"
HOST="${HOST:-127.0.0.1}"

# Function to print colored messages
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Function to generate a secure secret key
generate_secret_key() {
    if command -v openssl &> /dev/null; then
        openssl rand -hex 32
    elif command -v python3 &> /dev/null; then
        python3 -c "import secrets; print(secrets.token_hex(32))"
    else
        # Fallback to a basic method
        date +%s | sha256sum | base64 | head -c 64
    fi
}

# Navigate to backend directory
if [ ! -d "backend" ]; then
    log_error "Backend directory not found. Please run this script from the project root."
    exit 1
fi

cd backend
log_info "Working in backend directory..."

# Check for uv or fallback to pip
if command -v uv &> /dev/null; then
    PACKAGE_MANAGER="uv"
    log_info "Using uv package manager (fast!)"
else
    PACKAGE_MANAGER="pip"
    log_warning "uv not found, falling back to pip (slower). Install uv for better performance:"
    echo "       curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    log_info "Creating virtual environment..."
    if [ "$PACKAGE_MANAGER" = "uv" ]; then
        uv venv "$VENV_DIR"
    else
        python3 -m venv "$VENV_DIR"
    fi
    log_success "Virtual environment created"
else
    log_info "Virtual environment already exists"
fi

# Activate virtual environment
log_info "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source "$VENV_DIR/Scripts/activate"
else
    # Unix-like (Linux, macOS)
    source "$VENV_DIR/bin/activate"
fi
log_success "Virtual environment activated"

# Install/upgrade pip and setuptools for standard pip
if [ "$PACKAGE_MANAGER" = "pip" ]; then
    log_info "Upgrading pip and setuptools..."
    pip install --upgrade pip setuptools wheel &> /dev/null
fi

# Install or update dependencies
if [ -f "requirements.txt" ]; then
    log_info "Installing/updating dependencies..."
    
    if [ "$PACKAGE_MANAGER" = "uv" ]; then
        # Use uv pip install instead of sync to avoid removing needed packages
        uv pip install -r requirements.txt
    else
        # Check if requirements are already satisfied
        if pip freeze | grep -q "fastapi"; then
            log_info "Dependencies detected. Checking for updates..."
            pip install -r requirements.txt --upgrade
        else
            log_info "Installing dependencies for the first time..."
            pip install -r requirements.txt
        fi
    fi
    
    # Verify critical packages are installed
    if [ "$PACKAGE_MANAGER" = "uv" ]; then
        if ! uv pip show click &> /dev/null; then
            log_warning "Installing missing critical dependencies..."
            uv pip install click h11 httptools websockets watchfiles uvloop
        fi
    fi
    
    log_success "Dependencies ready"
else
    log_error "requirements.txt not found!"
    exit 1
fi

# Check for existing API keys in environment
check_api_keys() {
    local keys_found=""
    
    if [ -n "$OPENAI_API_KEY" ]; then
        keys_found="${keys_found}OpenAI "
    fi
    if [ -n "$ANTHROPIC_API_KEY" ] || [ -n "$CLAUDE_API_KEY" ]; then
        keys_found="${keys_found}Anthropic/Claude "
    fi
    if [ -n "$GEMINI_API_KEY" ] || [ -n "$GOOGLE_API_KEY" ]; then
        keys_found="${keys_found}Gemini "
    fi
    
    if [ -n "$keys_found" ]; then
        log_success "Found API keys in environment: $keys_found"
        return 0
    else
        return 1
    fi
}

# Create or update .env file
if [ ! -f "$ENV_FILE" ]; then
    log_info "Creating .env file..."
    
    # Generate secure secret key
    SECRET_KEY=$(generate_secret_key)
    
    # Check which API keys are available in environment
    OPENAI_KEY_LINE="# OPENAI_API_KEY=your-key-here  # Using from environment"
    ANTHROPIC_KEY_LINE="# ANTHROPIC_API_KEY=your-key-here  # Using from environment"
    GEMINI_KEY_LINE="# GEMINI_API_KEY=your-key-here  # Using from environment"
    
    if [ -z "$OPENAI_API_KEY" ]; then
        OPENAI_KEY_LINE="OPENAI_API_KEY=your-openai-key-here  # Set this or export as env var"
    fi
    if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$CLAUDE_API_KEY" ]; then
        ANTHROPIC_KEY_LINE="ANTHROPIC_API_KEY=your-anthropic-key-here  # Set this or export as env var"
    fi
    if [ -z "$GEMINI_API_KEY" ] && [ -z "$GOOGLE_API_KEY" ]; then
        GEMINI_KEY_LINE="GEMINI_API_KEY=your-gemini-key-here  # Set this or export as env var"
    fi
    
    cat > "$ENV_FILE" << EOF
# Curriculum Curator Configuration
# Generated on $(date)

# Security
SECRET_KEY=$SECRET_KEY
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=sqlite:///./curriculum_curator.db

# API Keys
# Note: API keys can be set here OR as environment variables
# Environment variables take precedence over .env file values
$OPENAI_KEY_LINE
$ANTHROPIC_KEY_LINE
$GEMINI_KEY_LINE

# Email Configuration (optional)
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=your-email@gmail.com
# SMTP_PASSWORD=your-app-password

# Email Whitelist (comma-separated)
EMAIL_WHITELIST=

# Server Configuration
DEBUG=True
EOF
    
    log_success ".env file created with secure defaults"
    
    # Check and report on API keys
    if check_api_keys; then
        log_info "Your existing environment API keys will be used automatically"
    else
        log_warning "No API keys found in environment. Add them to .env or export them"
    fi
else
    log_info ".env file already exists"
    
    # Check if user has API keys available
    if ! check_api_keys; then
        # Check if API keys are still default values in .env
        if grep -q "your-.*-key-here" "$ENV_FILE" 2>/dev/null; then
            log_warning "No API keys found. Set them in .env or export as environment variables"
        fi
    fi
fi

# Check if database migrations are needed (if using alembic)
if [ -d "alembic" ] && command -v alembic &> /dev/null; then
    log_info "Running database migrations..."
    alembic upgrade head
    log_success "Database migrations complete"
fi

# Create necessary directories
mkdir -p uploads logs data

# Check if port is already in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    log_error "Port $PORT is already in use!"
    read -p "Kill the process using this port? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        lsof -ti:$PORT | xargs kill -9
        log_success "Process killed"
    else
        log_error "Please free up port $PORT or specify a different port: PORT=8001 $0"
        exit 1
    fi
fi

# Start the server
log_success "Starting Curriculum Curator backend server..."
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🚀 Server running at: ${GREEN}http://$HOST:$PORT${NC}"
echo -e "${BLUE}📚 API Documentation: ${GREEN}http://$HOST:$PORT/docs${NC}"
echo -e "${BLUE}🔧 Alternative API Docs: ${GREEN}http://$HOST:$PORT/redoc${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Press CTRL+C to stop the server${NC}\n"

# Run the server with auto-reload for development
if command -v uvicorn &> /dev/null; then
    uvicorn app.main:app --reload --host "$HOST" --port "$PORT" --log-level info
else
    log_error "uvicorn not found. Please ensure dependencies were installed correctly."
    exit 1
fi