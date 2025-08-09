#!/usr/bin/env python3
"""
Generate a technical debt report in various formats
"""

import json
import re
from datetime import datetime
from pathlib import Path


class DebtScanner:
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.results = {
            "type_ignores": [],
            "skipped_tests": [],
            "todos": [],
            "empty_implementations": [],
            "security_exceptions": [],
        }

    def scan(self):
        """Scan the codebase for technical debt"""
        # Only scan relevant directories
        scan_dirs = ["app", "tests", "scripts"]
        exclude_patterns = ["__pycache__", ".venv", "venv", "env", ".git"]

        for scan_dir in scan_dirs:
            dir_path = self.root_path / scan_dir
            if not dir_path.exists():
                continue

            for py_file in dir_path.rglob("*.py"):
                # Skip excluded patterns
                if any(pattern in str(py_file) for pattern in exclude_patterns):
                    continue
                self._scan_file(py_file)

    def _scan_file(self, filepath: Path):
        """Scan a single file for debt markers"""
        try:
            with open(filepath, encoding="utf-8") as f:
                lines = f.readlines()

            for i, line in enumerate(lines, 1):
                # Type ignores
                if "# type: ignore" in line:
                    self.results["type_ignores"].append(
                        {
                            "file": str(filepath.relative_to(self.root_path)),
                            "line": i,
                            "content": line.strip(),
                            "has_explanation": bool(
                                re.search(r"# type: ignore.*[:-]", line)
                            ),
                        }
                    )

                # Skipped tests
                if "@pytest.mark.skip" in line:
                    reason = ""
                    if i < len(lines) and "reason=" in lines[i]:
                        reason = re.search(r'reason="([^"]*)"', lines[i])
                        reason = reason.group(1) if reason else ""
                    self.results["skipped_tests"].append(
                        {
                            "file": str(filepath.relative_to(self.root_path)),
                            "line": i,
                            "reason": reason,
                        }
                    )

                # TODOs
                if re.search(r"#\s*(TODO|FIXME|HACK|XXX)", line):
                    self.results["todos"].append(
                        {
                            "file": str(filepath.relative_to(self.root_path)),
                            "line": i,
                            "content": line.strip(),
                            "type": re.search(r"#\s*(TODO|FIXME|HACK|XXX)", line).group(
                                1
                            ),
                        }
                    )

                # Empty implementations
                if re.match(r"^\s*pass\s*$", line):
                    self.results["empty_implementations"].append(
                        {"file": str(filepath.relative_to(self.root_path)), "line": i}
                    )
        except Exception as e:
            print(f"Error scanning {filepath}: {e}")

    def generate_report(self, format: str = "markdown") -> str:
        """Generate report in specified format"""
        if format == "markdown":
            return self._generate_markdown_report()
        if format == "json":
            return json.dumps(self.results, indent=2)
        raise ValueError(f"Unknown format: {format}")

    def _generate_markdown_report(self) -> str:
        """Generate markdown report"""
        report = f"""# Technical Debt Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}

## Summary
- Type Ignores: {len(self.results["type_ignores"])}
- Skipped Tests: {len(self.results["skipped_tests"])}
- TODOs/FIXMEs: {len(self.results["todos"])}
- Empty Implementations: {len(self.results["empty_implementations"])}

## Risk Assessment
"""
        # Calculate risk score
        risk_score = 0
        if len(self.results["type_ignores"]) > 10:
            risk_score += 1
        if len(self.results["skipped_tests"]) > 5:
            risk_score += 1
        if len(self.results["todos"]) > 20:
            risk_score += 1

        risk_levels = ["LOW ✅", "MEDIUM ⚠️", "HIGH 🔴", "CRITICAL 🚨"]
        report += f"**{risk_levels[min(risk_score, 3)]}**\n\n"

        # Type ignores without explanation
        unexp_ignores = [
            x for x in self.results["type_ignores"] if not x["has_explanation"]
        ]
        if unexp_ignores:
            report += f"### ⚠️ Type Ignores Without Explanation: {len(unexp_ignores)}\n"
            for item in unexp_ignores[:5]:
                report += f"- `{item['file']}:{item['line']}`\n"
            if len(unexp_ignores) > 5:
                report += f"- ... and {len(unexp_ignores) - 5} more\n"
            report += "\n"

        # Skipped tests
        if self.results["skipped_tests"]:
            report += f"### Skipped Tests: {len(self.results['skipped_tests'])}\n"
            for item in self.results["skipped_tests"][:5]:
                report += (
                    f"- `{item['file']}:{item['line']}` {item['reason'][:50]}...\n"
                )
            report += "\n"

        # Old TODOs
        if self.results["todos"]:
            report += f"### Technical Debt Markers: {len(self.results['todos'])}\n"
            by_type = {}
            for todo in self.results["todos"]:
                by_type.setdefault(todo["type"], []).append(todo)
            for todo_type, items in by_type.items():
                report += f"- {todo_type}: {len(items)}\n"
            report += "\n"

        return report


def main():
    """Generate debt report"""
    scanner = DebtScanner()
    scanner.scan()

    # Generate reports
    print(scanner.generate_report("markdown"))

    # Save JSON for further processing
    with open("technical_debt.json", "w") as f:
        f.write(scanner.generate_report("json"))

    print("\n📊 Full report saved to technical_debt.json")


if __name__ == "__main__":
    main()
