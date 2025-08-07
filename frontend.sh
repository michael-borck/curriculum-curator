#!/usr/bin/env bash

# Robust Frontend Setup and Run Script for Curriculum Curator
# Handles Node.js, dependencies, and development server

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PORT="${VITE_PORT:-5173}"
HOST="${VITE_HOST:-localhost}"
API_URL="${VITE_API_URL:-http://localhost:8000}"
NODE_VERSION_REQUIRED="18.0.0"
PACKAGE_LOCK="package-lock.json"
NODE_MODULES="node_modules"
ENV_FILE=".env.local"

# Function to print colored messages
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_cyan() { echo -e "${CYAN}$1${NC}"; }

# Function to compare versions
version_compare() {
    if [[ $1 == $2 ]]; then
        return 0
    fi
    local IFS=.
    local i ver1=($1) ver2=($2)
    for ((i=${#ver1[@]}; i<${#ver2[@]}; i++)); do
        ver1[i]=0
    done
    for ((i=0; i<${#ver1[@]}; i++)); do
        if [[ -z ${ver2[i]} ]]; then
            ver2[i]=0
        fi
        if ((10#${ver1[i]} > 10#${ver2[i]})); then
            return 1
        fi
        if ((10#${ver1[i]} < 10#${ver2[i]})); then
            return 2
        fi
    done
    return 0
}

# Check if backend is running
check_backend() {
    if curl -s -o /dev/null -w "%{http_code}" "$API_URL" | grep -q "200\|404"; then
        log_success "Backend is running at $API_URL"
        return 0
    else
        log_warning "Backend not detected at $API_URL"
        log_info "Start the backend first with: ./backend.sh"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
        return 1
    fi
}

# Navigate to frontend directory
if [ ! -d "frontend" ]; then
    log_error "Frontend directory not found. Please run this script from the project root."
    exit 1
fi

cd frontend
log_info "Working in frontend directory..."

# Check Node.js installation
if ! command -v node &> /dev/null; then
    log_error "Node.js is not installed!"
    log_info "Please install Node.js from: https://nodejs.org/"
    log_info "Or use nvm: curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d 'v' -f 2)
version_compare "$NODE_VERSION" "$NODE_VERSION_REQUIRED" || RESULT=$?

if [ "${RESULT:-0}" -eq 2 ]; then
    log_warning "Node.js version $NODE_VERSION is older than recommended $NODE_VERSION_REQUIRED"
    log_info "Consider upgrading Node.js for better performance and compatibility"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    log_success "Node.js version $NODE_VERSION ✓"
fi

# Check for package manager preference
PACKAGE_MANAGER="npm"
USE_LOCKFILE=false

# Detect which package manager to use based on lockfiles
if [ -f "bun.lockb" ]; then
    if command -v bun &> /dev/null; then
        PACKAGE_MANAGER="bun"
        PACKAGE_LOCK="bun.lockb"
        USE_LOCKFILE=true
        log_info "Using Bun package manager (blazing fast! 🔥)"
    fi
elif [ -f "pnpm-lock.yaml" ]; then
    if command -v pnpm &> /dev/null; then
        PACKAGE_MANAGER="pnpm"
        PACKAGE_LOCK="pnpm-lock.yaml"
        USE_LOCKFILE=true
        log_info "Using pnpm package manager (efficient!)"
    fi
elif [ -f "yarn.lock" ]; then
    if command -v yarn &> /dev/null; then
        PACKAGE_MANAGER="yarn"
        PACKAGE_LOCK="yarn.lock"
        USE_LOCKFILE=true
        log_info "Using Yarn package manager"
    fi
elif [ -f "package-lock.json" ]; then
    USE_LOCKFILE=true
    log_info "Using npm package manager"
else
    log_info "No lockfile found, will create one with $PACKAGE_MANAGER"
fi

# Check if package.json exists
if [ ! -f "package.json" ]; then
    log_error "package.json not found!"
    exit 1
fi

# Create .env.local if it doesn't exist
if [ ! -f "$ENV_FILE" ]; then
    log_info "Creating .env.local file..."
    cat > "$ENV_FILE" << EOF
# Frontend Environment Variables
# Generated on $(date)

# API Configuration
VITE_API_URL=$API_URL

# Optional: Override default ports
# VITE_PORT=$PORT
# VITE_HOST=$HOST

# Feature Flags (optional)
VITE_ENABLE_AI_FEATURES=true
VITE_ENABLE_FILE_UPLOAD=true

# Development
VITE_DEBUG=false
EOF
    log_success ".env.local created with defaults"
else
    log_info ".env.local already exists"
fi

# Function to install dependencies
install_dependencies() {
    case $PACKAGE_MANAGER in
        bun)
            bun install
            ;;
        pnpm)
            pnpm install
            ;;
        yarn)
            yarn install
            ;;
        npm)
            if [ "$USE_LOCKFILE" = true ] && [ -f "$PACKAGE_LOCK" ]; then
                # Try npm ci first for speed, fall back to npm install if it fails
                log_info "Attempting fast install with npm ci..."
                if npm ci 2>/dev/null; then
                    log_success "Fast install completed"
                else
                    log_warning "Lock file out of sync, updating dependencies..."
                    npm install
                    log_success "Dependencies synchronized"
                fi
            else
                npm install
            fi
            ;;
    esac
}

# Check if dependencies need to be installed or updated
NEED_INSTALL=false

if [ ! -d "$NODE_MODULES" ]; then
    log_info "Node modules not found. Installing dependencies..."
    NEED_INSTALL=true
elif [ ! -f "$PACKAGE_LOCK" ]; then
    log_info "No lockfile found. Installing dependencies..."
    NEED_INSTALL=true
elif [ "package.json" -nt "$NODE_MODULES" ]; then
    log_info "package.json has been modified. Updating dependencies..."
    NEED_INSTALL=true
elif [ "$PACKAGE_LOCK" -nt "$NODE_MODULES" ] && [ "$USE_LOCKFILE" = true ]; then
    log_info "Lockfile has been updated. Syncing dependencies..."
    NEED_INSTALL=true
else
    log_success "Dependencies are up to date"
fi

if [ "$NEED_INSTALL" = true ]; then
    log_info "Installing/updating dependencies with $PACKAGE_MANAGER..."
    install_dependencies
    log_success "Dependencies installed successfully"
fi

# Check if port is already in use
check_port() {
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_warning "Port $PORT is already in use!"
        
        # Check if it's already our dev server
        if curl -s -o /dev/null "http://localhost:$PORT"; then
            log_info "Seems like the dev server is already running"
            log_cyan "Open http://localhost:$PORT in your browser"
            read -p "Kill existing server and restart? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
                sleep 1
                return 0
            else
                exit 0
            fi
        else
            read -p "Kill the process using port $PORT? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
                sleep 1
                log_success "Port $PORT freed"
            else
                # Find next available port
                for ((p=$PORT; p<=9999; p++)); do
                    if ! lsof -Pi :$p -sTCP:LISTEN -t >/dev/null 2>&1; then
                        PORT=$p
                        log_info "Using alternative port: $PORT"
                        break
                    fi
                done
            fi
        fi
    fi
}

# Clear terminal for cleaner output
clear

# Print banner
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}     🎓 Curriculum Curator - Frontend${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo

# Check if backend is running
check_backend

# Check port availability
check_port

# Build check for production
if [ "$NODE_ENV" = "production" ]; then
    log_info "Building for production..."
    case $PACKAGE_MANAGER in
        bun) bun run build ;;
        pnpm) pnpm build ;;
        yarn) yarn build ;;
        npm) npm run build ;;
    esac
    log_success "Production build complete in ./dist"
    exit 0
fi

# Start the development server
log_success "Starting Curriculum Curator frontend..."
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🚀 Frontend will start at: ${GREEN}http://$HOST:$PORT${NC}"
echo -e "${BLUE}🔗 Backend API expected at: ${GREEN}$API_URL${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Press CTRL+C to stop the server${NC}\n"

# Function to open browser (cross-platform)
open_browser() {
    sleep 2  # Wait for server to start
    URL="http://$HOST:$PORT"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "$URL"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open "$URL" 2>/dev/null || true
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
        start "$URL"
    fi
}

# Open browser in background (optional)
if [ "$AUTO_OPEN_BROWSER" = "true" ]; then
    open_browser &
fi

# Run the development server
case $PACKAGE_MANAGER in
    bun)
        bun run dev --port $PORT --host $HOST
        ;;
    pnpm)
        pnpm dev -- --port $PORT --host $HOST
        ;;
    yarn)
        yarn dev --port $PORT --host $HOST
        ;;
    npm)
        npm run dev -- --port $PORT --host $HOST
        ;;
esac