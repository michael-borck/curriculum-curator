"""
Code Formatter Plugin.

Formats code blocks in markdown content with proper syntax highlighting and indentation
"""

import json
import re
from typing import Any

from app.plugins.base import PluginResult, RemediatorPlugin


class CodeFormatter(RemediatorPlugin):
    """Formats and validates code blocks in content."""

    @property
    def name(self) -> str:
        """Return plugin name."""
        return "code_formatter"

    @property
    def description(self) -> str:
        """Return plugin description."""
        return "Formats code blocks with syntax highlighting and proper indentation"

    def _extract_code_blocks(self, content: str) -> list[dict[str, Any]]:
        """Extract all code blocks from content."""
        code_blocks = []

        # Pattern for fenced code blocks ```language\ncode\n```
        pattern = r"```(\w*)\n(.*?)```"
        matches = re.finditer(pattern, content, re.DOTALL)

        for match in matches:
            language = match.group(1) or "text"
            code = match.group(2)
            code_blocks.append(
                {
                    "language": language,
                    "code": code,
                    "start": match.start(),
                    "end": match.end(),
                    "full_match": match.group(0),
                }
            )

        # Also find inline code blocks without language
        pattern_no_lang = r"```\n(.*?)```"
        matches_no_lang = re.finditer(pattern_no_lang, content, re.DOTALL)

        for match in matches_no_lang:
            # Check if this isn't already captured
            if not any(
                match.start() >= b["start"] and match.end() <= b["end"]
                for b in code_blocks
            ):
                code = match.group(1)
                code_blocks.append(
                    {
                        "language": self._detect_language(code),
                        "code": code,
                        "start": match.start(),
                        "end": match.end(),
                        "full_match": match.group(0),
                    }
                )

        return sorted(code_blocks, key=lambda x: x["start"])

    def _detect_language(self, code: str) -> str:
        """Detect programming language from code content."""
        # Language detection rules
        language_rules = {
            "python": ["def ", "import ", "from ", "class ", "if __name__"],
            "javascript": ["const ", "let ", "var ", "function ", "=>"],
            "java": ["public class ", "public static void main"],
            "sql": ["select ", "from ", "where ", "insert ", "update "],
            "bash": ["echo ", "cd ", "ls ", "mkdir "],
        }

        code_lower = code.lower()

        # Check each language rule
        for language, keywords in language_rules.items():
            if language == "sql":
                # SQL keywords should be case-insensitive
                if any(keyword in code_lower for keyword in keywords):
                    return language
            elif any(keyword in code for keyword in keywords):
                # Special handling for TypeScript
                if language == "javascript" and ("interface " in code or ": string" in code or ": number" in code):
                    return "typescript"
                return language

        # Check for special patterns
        special_lang = self._check_special_languages(code, code_lower)
        if special_lang:
            return special_lang

        return "text"

    def _check_special_languages(self, code: str, code_lower: str) -> str | None:  # noqa: PLR0911
        """Check for languages that require special pattern matching."""
        # C/C++
        if "#include" in code:
            return "cpp" if "cout" in code or "namespace" in code else "c"

        # HTML
        if "<html" in code_lower or "<div" in code_lower or "<body" in code_lower:
            return "html"

        # CSS
        if "{" in code and "}" in code and "color:" in code_lower:
            return "css"

        # JSON
        try:
            json.loads(code)
            return "json"
        except Exception:
            pass

        # Shell script
        if code.startswith("#!"):
            return "bash"

        # YAML
        if ":" in code and "-" in code and "{" not in code:
            lines = code.split("\n")
            if any(":" in line for line in lines):
                return "yaml"

        return None

    def _format_python(self, code: str) -> str:
        """Format Python code."""
        try:
            # Basic Python formatting without external dependencies
            lines = code.split("\n")
            formatted_lines = []
            indent_level = 0

            for line in lines:
                stripped = line.strip()

                # Skip empty lines
                if not stripped:
                    formatted_lines.append("")
                    continue

                # Decrease indent for these keywords
                if stripped.startswith(("return", "break", "continue", "pass")) and indent_level > 0:
                    indent_level -= 1

                # Decrease indent for dedent keywords
                if stripped.startswith(
                    ("else:", "elif ", "except:", "finally:", "except ")
                ) and indent_level > 0:
                    indent_level -= 1

                # Add proper indentation
                formatted_line = "    " * indent_level + stripped
                formatted_lines.append(formatted_line)

                # Increase indent after these patterns
                if stripped.endswith(":"):
                    indent_level += 1

                # Reset indent after return
                if stripped.startswith("return"):
                    indent_level = max(0, indent_level - 1)

            return "\n".join(formatted_lines)
        except Exception:
            return code  # Return original if formatting fails

    def _format_javascript(self, code: str) -> str:
        """Format JavaScript/TypeScript code."""
        try:
            lines = code.split("\n")
            formatted_lines = []
            indent_level = 0

            for line in lines:
                stripped = line.strip()

                if not stripped:
                    formatted_lines.append("")
                    continue

                # Count braces
                open_braces = stripped.count("{") - stripped.count("}")

                # Decrease indent for closing braces
                if stripped.startswith("}"):
                    indent_level = max(0, indent_level - 1)

                # Add indentation
                formatted_line = "  " * indent_level + stripped
                formatted_lines.append(formatted_line)

                # Adjust indent level
                indent_level = max(0, indent_level + open_braces)

            return "\n".join(formatted_lines)
        except Exception:
            return code

    def _format_json(self, code: str) -> str:
        """Format JSON code."""
        try:
            # Parse and pretty-print JSON
            data = json.loads(code)
            return json.dumps(data, indent=2, sort_keys=False)
        except Exception:
            return code

    def _format_sql(self, code: str) -> str:
        """Format SQL code."""
        try:
            # Basic SQL formatting
            keywords = [
                "SELECT",
                "FROM",
                "WHERE",
                "JOIN",
                "LEFT JOIN",
                "RIGHT JOIN",
                "INNER JOIN",
                "ON",
                "GROUP BY",
                "ORDER BY",
                "HAVING",
                "INSERT INTO",
                "VALUES",
                "UPDATE",
                "SET",
                "DELETE",
            ]

            formatted = code
            for keyword in keywords:
                # Add newline before major keywords
                if keyword in ["FROM", "WHERE", "GROUP BY", "ORDER BY", "HAVING"]:
                    formatted = re.sub(
                        rf"\s+{keyword}\s+",
                        f"\n{keyword} ",
                        formatted,
                        flags=re.IGNORECASE,
                    )
                else:
                    # Just uppercase the keyword
                    formatted = re.sub(
                        rf"\b{keyword}\b", keyword, formatted, flags=re.IGNORECASE
                    )

            # Clean up multiple spaces
            formatted = re.sub(r" +", " ", formatted)

            return formatted.strip()
        except Exception:
            return code

    def _format_code(self, code: str, language: str) -> str:
        """Format code based on language."""
        # Remove trailing whitespace from each line
        lines = code.split("\n")
        lines = [line.rstrip() for line in lines]
        code = "\n".join(lines)

        # Language-specific formatting
        if language in ["python", "py"]:
            return self._format_python(code)
        if language in ["javascript", "js", "typescript", "ts"]:
            return self._format_javascript(code)
        if language == "json":
            return self._format_json(code)
        if language == "sql":
            return self._format_sql(code)
        # Basic formatting for other languages
        return code.strip()

    def _add_language_if_missing(self, content: str) -> str:
        """Add language identifier to code blocks that don't have one."""

        def replace_block(match):
            code = match.group(1)
            language = self._detect_language(code)
            return f"```{language}\n{code}```"

        # Replace code blocks without language
        return re.sub(r"```\n(.*?)```", replace_block, content, flags=re.DOTALL)

    async def remediate(self, content: str, issues: list) -> PluginResult:
        """Format code blocks in content."""
        try:
            # Extract options from issues
            options = {}
            for issue in issues:
                if isinstance(issue, dict):
                    options.update(issue)

            add_language = options.get("add_language", True)
            format_code = options.get("format_code", True)
            fix_indentation = options.get("fix_indentation", True)

            # Extract code blocks
            code_blocks = self._extract_code_blocks(content)

            if not code_blocks:
                return PluginResult(
                    success=True,
                    message="No code blocks found to format",
                    data={"skipped": True, "code_blocks": 0},
                )

            # Process content
            new_content = content
            offset = 0
            formatted_count = 0

            for block in code_blocks:
                if format_code:
                    # Format the code
                    formatted_code = self._format_code(block["code"], block["language"])

                    # Only update if changed
                    if formatted_code != block["code"]:
                        # Create new code block
                        new_block = f"```{block['language']}\n{formatted_code}\n```"

                        # Replace in content
                        start = block["start"] + offset
                        end = block["end"] + offset
                        new_content = (
                            new_content[:start] + new_block + new_content[end:]
                        )

                        # Update offset for next blocks
                        offset += len(new_block) - len(block["full_match"])
                        formatted_count += 1

            # Add language identifiers if requested
            if add_language:
                new_content = self._add_language_if_missing(new_content)

            # Statistics
            languages = {}
            for block in code_blocks:
                lang = block["language"]
                languages[lang] = languages.get(lang, 0) + 1

            return PluginResult(
                success=True,
                message=f"Formatted {formatted_count} of {len(code_blocks)} code blocks",
                data={
                    "content": new_content,
                    "code_blocks_found": len(code_blocks),
                    "code_blocks_formatted": formatted_count,
                    "languages": languages,
                    "actions_taken": {
                        "formatting": format_code,
                        "language_detection": add_language,
                        "indentation_fix": fix_indentation,
                    },
                },
                suggestions=None,
            )

        except Exception as e:
            return PluginResult(
                success=False,
                message=f"Code formatting failed: {e!s}",
            )
