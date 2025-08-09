#!/bin/bash

# Technical Debt Audit Script
# Scans codebase for various exceptions and workarounds

echo "=== Technical Debt Audit Report ==="
echo "Generated: $(date)"
echo

# Function to count occurrences (excluding binary files)
count_pattern() {
    local pattern="$1"
    local path="$2"
    local count=$(find "$path" -name "*.py" -type f -exec grep -H "$pattern" {} \; 2>/dev/null | wc -l)
    echo "$count"
}

# Function to find files with pattern (excluding binary files)
find_pattern_files() {
    local pattern="$1"
    local path="$2"
    find "$path" -name "*.py" -type f -exec grep -l "$pattern" {} \; 2>/dev/null | sort
}

echo "## Type Checking Exceptions"
echo "### Total '# type: ignore' comments: $(count_pattern '# type: ignore' app/)"
echo "Files with type ignores:"
find_pattern_files '# type: ignore' app/ | while read -r file; do
    count=$(grep -c '# type: ignore' "$file")
    echo "  - $file: $count occurrences"
done
echo

echo "## Commented Out Code"
echo "### Commented decorators (potential issues):"
grep -r -n '@.*#' app/ | grep -E '(limit|limiter|rate)' || echo "  None found"
echo

echo "## TODO/FIXME/HACK Comments"
echo "### TODO: $(count_pattern 'TODO' app/)"
echo "### FIXME: $(count_pattern 'FIXME' app/)"
echo "### HACK: $(count_pattern 'HACK' app/)"
echo "### XXX: $(count_pattern 'XXX' app/)"
echo "Files with technical debt markers:"
find_pattern_files 'TODO\|FIXME\|HACK\|XXX' app/ | while read -r file; do
    echo "  - $file"
done
echo

echo "## Test Exceptions"
echo "### Skipped tests: $(count_pattern '@pytest.mark.skip' tests/)"
echo "### Tests with skip:"
find_pattern_files '@pytest.mark.skip' tests/ | while read -r file; do
    count=$(grep -c '@pytest.mark.skip' "$file")
    echo "  - $file: $count skipped tests"
done
echo

echo "## Security Workarounds"
echo "### Files with 'disable' or 'bypass':"
grep -r -i -n 'disable\|bypass' app/ | grep -v -E '(test|spec)' | head -10 || echo "  None found"
echo

echo "## Import Workarounds"
echo "### Mock imports in tests:"
grep -r "sys.modules\[" tests/ | wc -l | xargs echo "Total mocked modules:"
echo

echo "## Linting Exceptions"
echo "### noqa comments: $(count_pattern '# noqa' app/)"
echo "### pylint disable: $(count_pattern 'pylint: disable' app/)"
echo "### ruff ignore: $(count_pattern '# ruff: ignore' app/)"
echo

echo "## Empty Implementations"
echo "### Files with 'pass' statements (potential stubs):"
find app/ -name "*.py" -exec grep -l "^[[:space:]]*pass[[:space:]]*$" {} \; | head -10
echo

echo "## Risk Assessment"
type_ignores=$(count_pattern '# type: ignore' app/)
skipped_tests=$(count_pattern '@pytest.mark.skip' tests/)
todos=$(count_pattern 'TODO\|FIXME' app/)

risk_score=0
[[ $type_ignores -gt 10 ]] && risk_score=$((risk_score + 1))
[[ $skipped_tests -gt 5 ]] && risk_score=$((risk_score + 1))
[[ $todos -gt 20 ]] && risk_score=$((risk_score + 1))

echo "### Risk Level: "
case $risk_score in
    0) echo "LOW - Good job keeping technical debt under control!" ;;
    1) echo "MEDIUM - Some areas need attention" ;;
    2) echo "HIGH - Technical debt is accumulating" ;;
    *) echo "CRITICAL - Immediate attention needed" ;;
esac

echo
echo "=== End of Report ==="