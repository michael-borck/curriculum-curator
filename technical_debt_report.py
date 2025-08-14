#!/usr/bin/env python3
"""
Technical Debt Report Generator

Analyzes codebase for suppressed linting violations and generates a comprehensive report.
Tracks both backend (Python/ruff) and frontend (TypeScript/ESLint) technical debt.
"""

import json
import re
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


class TechnicalDebtAnalyzer:
    """Analyze and report on technical debt from suppressed linting violations."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_path = project_root / "backend"
        self.frontend_path = project_root / "frontend"
        self.report = {
            "generated_at": datetime.now().isoformat(),
            "backend": {"python": {}},
            "frontend": {"typescript": {}},
            "summary": {},
        }

    def analyze_python_noqa(self) -> dict[str, Any]:
        """Analyze Python files for noqa comments."""
        noqa_stats = defaultdict(list)
        total_suppressions = 0

        # Pattern to match noqa comments with specific codes
        noqa_pattern = re.compile(r"#\s*noqa:\s*([A-Z0-9]+(?:,\s*[A-Z0-9]+)*)")
        
        # Find all Python files (excluding virtual environments)
        for py_file in self.backend_path.rglob("*.py"):
            # Skip virtual environment directories
            if ".venv" in str(py_file) or "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
            relative_path = py_file.relative_to(self.backend_path)
            
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        match = noqa_pattern.search(line)
                        if match:
                            codes = [c.strip() for c in match.group(1).split(",")]
                            for code in codes:
                                noqa_stats[code].append({
                                    "file": str(relative_path),
                                    "line": line_num,
                                    "context": line.strip()[:100]  # First 100 chars
                                })
                                total_suppressions += 1
            except Exception as e:
                print(f"Error reading {py_file}: {e}")

        return {
            "suppressions_by_code": dict(noqa_stats),
            "total_suppressions": total_suppressions,
            "unique_codes": len(noqa_stats),
            "files_with_suppressions": len(set(
                item["file"] 
                for items in noqa_stats.values() 
                for item in items
            ))
        }

    def analyze_typescript_suppressions(self) -> dict[str, Any]:
        """Analyze TypeScript/JavaScript files for ESLint disable comments."""
        eslint_stats = defaultdict(list)
        total_suppressions = 0

        # Patterns for ESLint disable comments
        patterns = [
            re.compile(r"//\s*eslint-disable-next-line\s*(.*)"),
            re.compile(r"//\s*eslint-disable\s+(.*)"),
            re.compile(r"/\*\s*eslint-disable\s+(.*?)\s*\*/"),
            re.compile(r"//\s*@ts-ignore"),
            re.compile(r"//\s*@ts-nocheck"),
            re.compile(r"//\s*@ts-expect-error"),
        ]

        # Find all TS/TSX/JS/JSX files
        for ext in ["*.ts", "*.tsx", "*.js", "*.jsx"]:
            for file_path in self.frontend_path.rglob(ext):
                # Skip node_modules and build directories
                if "node_modules" in str(file_path) or "dist" in str(file_path):
                    continue
                    
                relative_path = file_path.relative_to(self.frontend_path)
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        for line_num, line in enumerate(f, 1):
                            for pattern in patterns:
                                match = pattern.search(line)
                                if match:
                                    # Extract the specific rule if mentioned
                                    rule = match.group(1) if match.lastindex else "general"
                                    rule = rule.strip() if rule else "general"
                                    
                                    # Handle TypeScript-specific suppressions
                                    if "@ts-" in line:
                                        rule = "typescript-" + match.group(0).split("@ts-")[1].split()[0]
                                    
                                    eslint_stats[rule].append({
                                        "file": str(relative_path),
                                        "line": line_num,
                                        "context": line.strip()[:100]
                                    })
                                    total_suppressions += 1
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

        return {
            "suppressions_by_rule": dict(eslint_stats),
            "total_suppressions": total_suppressions,
            "unique_rules": len(eslint_stats),
            "files_with_suppressions": len(set(
                item["file"] 
                for items in eslint_stats.values() 
                for item in items
            ))
        }

    def get_ruff_statistics(self) -> dict[str, Any]:
        """Get ruff statistics including ignored violations."""
        try:
            # Run ruff with statistics
            result = subprocess.run(
                ["ruff", "check", ".", "--statistics", "--output-format", "json"],
                cwd=self.backend_path,
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                return json.loads(result.stdout)
        except (subprocess.SubprocessError, json.JSONDecodeError) as e:
            print(f"Error getting ruff statistics: {e}")
        
        return {}

    def get_eslint_statistics(self) -> dict[str, Any]:
        """Get ESLint statistics."""
        try:
            # Run ESLint with JSON output
            result = subprocess.run(
                ["npm", "run", "lint", "--", "--format", "json"],
                cwd=self.frontend_path,
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                data = json.loads(result.stdout)
                # Process ESLint output to get statistics
                stats = defaultdict(int)
                for file_result in data:
                    for message in file_result.get("messages", []):
                        if message.get("ruleId"):
                            stats[message["ruleId"]] += 1
                return dict(stats)
        except (subprocess.SubprocessError, json.JSONDecodeError) as e:
            print(f"Error getting ESLint statistics: {e}")
        
        return {}

    def generate_markdown_report(self) -> str:
        """Generate a markdown report of technical debt."""
        lines = [
            "# Technical Debt Report",
            f"\n📅 Generated: {self.report['generated_at']}",
            "\n## Executive Summary\n",
        ]

        # Summary statistics
        backend_total = self.report["backend"]["python"].get("total_suppressions", 0)
        frontend_total = self.report["frontend"]["typescript"].get("total_suppressions", 0)
        
        lines.extend([
            f"- **Total Suppressions**: {backend_total + frontend_total}",
            f"  - Backend (Python): {backend_total}",
            f"  - Frontend (TypeScript): {frontend_total}",
            ""
        ])

        # Backend section
        lines.append("\n## Backend (Python/Ruff)\n")
        
        if self.report["backend"]["python"].get("suppressions_by_code"):
            lines.append("### Suppressed Violations by Code\n")
            
            # Sort by frequency
            suppressions = self.report["backend"]["python"]["suppressions_by_code"]
            sorted_codes = sorted(suppressions.items(), key=lambda x: len(x[1]), reverse=True)
            
            lines.append("| Code | Count | Description | Priority |")
            lines.append("|------|-------|-------------|----------|")
            
            # Code descriptions and priorities (you can expand this)
            code_info = {
                "PLR0911": ("Too many return statements", "Medium"),
                "ERA001": ("Commented-out code", "Low"),
                "RUF001": ("String contains ambiguous character", "Low"),
                "N806": ("Variable name not in lowercase", "Low"),
                "A002": ("Builtin shadowing", "Medium"),
                "E722": ("Bare except clause", "High"),
                "PLW2901": ("Loop variable overwritten", "Medium"),
            }
            
            for code, occurrences in sorted_codes[:10]:  # Top 10
                desc, priority = code_info.get(code, ("Unknown", "Low"))
                lines.append(f"| {code} | {len(occurrences)} | {desc} | {priority} |")
            
            # Detailed occurrences for high-priority items
            lines.append("\n### High Priority Items\n")
            high_priority_codes = [code for code, (_, priority) in code_info.items() if priority == "High"]
            
            for code in high_priority_codes:
                if code in suppressions:
                    lines.append(f"\n#### {code} - {code_info[code][0]}\n")
                    for item in suppressions[code][:5]:  # Show first 5
                        lines.append(f"- `{item['file']}:{item['line']}`")

        # Frontend section
        lines.append("\n## Frontend (TypeScript/ESLint)\n")
        
        if self.report["frontend"]["typescript"].get("suppressions_by_rule"):
            lines.append("### Suppressed Violations by Rule\n")
            
            suppressions = self.report["frontend"]["typescript"]["suppressions_by_rule"]
            sorted_rules = sorted(suppressions.items(), key=lambda x: len(x[1]), reverse=True)
            
            lines.append("| Rule | Count | Type |")
            lines.append("|------|-------|------|")
            
            for rule, occurrences in sorted_rules[:10]:
                rule_type = "TypeScript" if "typescript" in rule else "ESLint"
                lines.append(f"| {rule} | {len(occurrences)} | {rule_type} |")

        # Recommendations
        lines.extend([
            "\n## Recommendations\n",
            "1. **Address High Priority Items First**: Focus on security and stability issues",
            "2. **Schedule Refactoring**: Allocate time in sprints for debt reduction",
            "3. **Document Suppressions**: Add comments explaining why each suppression is necessary",
            "4. **Track Trends**: Run this report regularly to ensure debt doesn't grow",
            "5. **Set Thresholds**: Establish maximum acceptable suppression counts",
        ])

        # Files with most suppressions
        lines.append("\n## Files with Most Technical Debt\n")
        
        # Collect all files
        file_counts = defaultdict(int)
        
        if self.report["backend"]["python"].get("suppressions_by_code"):
            for occurrences in self.report["backend"]["python"]["suppressions_by_code"].values():
                for item in occurrences:
                    file_counts[f"backend/{item['file']}"] += 1
                    
        if self.report["frontend"]["typescript"].get("suppressions_by_rule"):
            for occurrences in self.report["frontend"]["typescript"]["suppressions_by_rule"].values():
                for item in occurrences:
                    file_counts[f"frontend/{item['file']}"] += 1
        
        # Top 10 files
        top_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        lines.append("| File | Suppressions |")
        lines.append("|------|--------------|")
        for file_path, count in top_files:
            lines.append(f"| {file_path} | {count} |")

        return "\n".join(lines)

    def generate_json_report(self) -> str:
        """Generate a JSON report for programmatic processing."""
        return json.dumps(self.report, indent=2)

    def run(self, output_format: str = "markdown") -> str:
        """Run the analysis and generate report."""
        print("🔍 Analyzing backend Python code...")
        self.report["backend"]["python"] = self.analyze_python_noqa()
        
        print("🔍 Analyzing frontend TypeScript code...")
        self.report["frontend"]["typescript"] = self.analyze_typescript_suppressions()
        
        # Calculate summary
        self.report["summary"] = {
            "total_suppressions": (
                self.report["backend"]["python"].get("total_suppressions", 0) +
                self.report["frontend"]["typescript"].get("total_suppressions", 0)
            ),
            "backend_files_affected": self.report["backend"]["python"].get("files_with_suppressions", 0),
            "frontend_files_affected": self.report["frontend"]["typescript"].get("files_with_suppressions", 0),
        }
        
        if output_format == "json":
            return self.generate_json_report()
        else:
            return self.generate_markdown_report()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate technical debt report")
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)"
    )
    parser.add_argument(
        "--output",
        help="Output file (default: stdout)"
    )
    
    args = parser.parse_args()
    
    # Find project root (same directory as this script)
    current_path = Path(__file__).resolve().parent
    
    analyzer = TechnicalDebtAnalyzer(current_path)
    report = analyzer.run(args.format)
    
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report)
        print(f"✅ Report saved to {output_path}")
    else:
        print(report)


if __name__ == "__main__":
    main()