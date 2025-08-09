#!/bin/bash

# Pre-commit hook to check for technical debt additions
# Copy this to .git/hooks/pre-commit and make executable

echo "Checking for technical debt markers..."

# Check staged Python files for new debt markers
staged_files=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')

if [ -z "$staged_files" ]; then
    exit 0
fi

debt_found=0
warnings=""

for file in $staged_files; do
    # Check for type: ignore without explanation
    if git diff --cached "$file" | grep -E '^\+.*# type: ignore\s*$' > /dev/null; then
        warnings="$warnings\n⚠️  $file: Found 'type: ignore' without explanation"
        debt_found=1
    fi
    
    # Check for TODO without date/owner
    if git diff --cached "$file" | grep -E '^\+.*# TODO[^(]' > /dev/null; then
        warnings="$warnings\n⚠️  $file: Found TODO without (owner, date) format"
        debt_found=1
    fi
    
    # Check for skipped tests without reason
    if git diff --cached "$file" | grep -E '^\+.*@pytest\.mark\.skip\s*$' > /dev/null; then
        warnings="$warnings\n⚠️  $file: Found skip without reason"
        debt_found=1
    fi
    
    # Check for commented out code that looks like decorators
    if git diff --cached "$file" | grep -E '^\+.*#.*@[a-zA-Z_]+' > /dev/null; then
        warnings="$warnings\n⚠️  $file: Found commented decorator - possible workaround"
        debt_found=1
    fi
done

if [ $debt_found -eq 1 ]; then
    echo -e "\n❌ Technical debt detected in staged files:"
    echo -e "$warnings"
    echo -e "\nPlease follow guidelines in CODING_STANDARDS.md:"
    echo "  - Add explanations to type: ignore comments"
    echo "  - Use TODO(owner, YYYY-MM-DD) format"
    echo "  - Add reason to @pytest.mark.skip"
    echo "  - Document any workarounds in TECHNICAL_DEBT.md"
    echo -e "\nCommit anyway? (y/n): \c"
    read answer
    if [ "$answer" != "y" ]; then
        exit 1
    fi
fi

echo "✅ Technical debt check passed"
exit 0