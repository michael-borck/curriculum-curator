#!/bin/bash
# Technical Debt Report Generator
# Analyzes suppressed linting violations across the entire codebase

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}📊 Technical Debt Report Generator${NC}"
echo "=================================="
echo ""

# Default values
FORMAT="markdown"
OUTPUT=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --json)
            FORMAT="json"
            shift
            ;;
        --output)
            OUTPUT="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --json              Output in JSON format (default: markdown)"
            echo "  --output <file>     Save to file (default: stdout)"
            echo "  --help              Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Show markdown report"
            echo "  $0 --json                             # Show JSON report"
            echo "  $0 --output reports/tech-debt.md     # Save markdown to file"
            echo "  $0 --json --output reports/debt.json # Save JSON to file"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Run the Python script
if [ -n "$OUTPUT" ]; then
    python3 technical_debt_report.py --format "$FORMAT" --output "$OUTPUT"
else
    python3 technical_debt_report.py --format "$FORMAT"
fi

# Quick stats if running interactively (no output file)
if [ -z "$OUTPUT" ]; then
    echo ""
    echo -e "${YELLOW}Quick Actions:${NC}"
    echo "1. To see only Python noqa comments:"
    echo "   grep -r '# noqa:' backend/ --include='*.py'"
    echo ""
    echo "2. To see only TypeScript suppressions:"
    echo "   grep -r '// eslint-disable' frontend/src/ --include='*.ts*'"
    echo ""
    echo "3. To check specific violation codes in Python:"
    echo "   ruff check backend/ --select=RUF100"
fi