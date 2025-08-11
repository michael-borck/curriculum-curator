"""
Grammar Validator Plugin
Basic grammar and style checking
"""

import re
from typing import Any

from app.plugins.base import PluginResult, ValidatorPlugin


class GrammarValidator(ValidatorPlugin):
    """Validates content for grammar and style issues"""

    @property
    def name(self) -> str:
        return "grammar_validator"

    @property
    def description(self) -> str:
        return "Checks for common grammar and style issues"

    def _check_passive_voice(self, content: str) -> tuple[list[str], list[str]]:
        """Detect passive voice constructions"""
        issues = []
        suggestions = []

        # Common passive voice patterns
        passive_patterns = [
            r"\b(was|were|been|being|is|are|am)\s+\w+ed\b",
            r"\b(was|were|been|being|is|are|am)\s+\w+en\b",
            r"\bby\s+\w+\s+(was|were|been|being|is|are|am)\b",
        ]

        sentences = re.split(r"[.!?]+", content)
        for sentence in sentences:
            for pattern in passive_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    if len(sentence) < 100:  # Only show short sentences
                        issues.append(f"Possible passive voice: '{sentence.strip()}'")
                        suggestions.append(
                            "Consider rewriting in active voice for clarity and directness"
                        )
                    break

        return issues[:5], suggestions[:5]  # Limit to 5 to avoid overwhelming

    def _check_sentence_starters(self, content: str) -> tuple[list[str], list[str]]:
        """Check for repetitive sentence starters"""
        issues = []
        suggestions = []

        sentences = re.split(r"[.!?]+", content)
        starters = []

        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                # Get first word
                first_word = sentence.split()[0] if sentence.split() else ""
                if first_word:
                    starters.append(first_word.lower())

        # Check for repetition
        for i in range(len(starters) - 2):
            if starters[i] == starters[i+1] == starters[i+2]:
                issues.append(
                    f"Three consecutive sentences start with '{starters[i].capitalize()}'"
                )
                suggestions.append(
                    "Vary sentence beginnings to improve flow"
                )
                break  # Only report once

        return issues, suggestions

    def _check_wordiness(self, content: str) -> tuple[list[str], list[str]]:
        """Check for wordy phrases"""
        issues = []
        suggestions = []

        wordy_phrases = {
            "at this point in time": "now",
            "at the present time": "now",
            "in order to": "to",
            "due to the fact that": "because",
            "in the event that": "if",
            "for the purpose of": "to",
            "with regard to": "about",
            "in spite of the fact that": "although",
            "as a result of": "because",
            "in the near future": "soon",
            "at all times": "always",
            "in most cases": "usually",
            "in the process of": "currently",
            "make use of": "use",
            "prior to": "before",
        }

        content_lower = content.lower()
        for wordy, concise in wordy_phrases.items():
            if wordy in content_lower:
                issues.append(f"Wordy phrase found: '{wordy}'")
                suggestions.append(f"Replace '{wordy}' with '{concise}'")

        return issues[:5], suggestions[:5]  # Limit to 5

    def _check_spelling_common_errors(self, content: str) -> tuple[list[str], list[str]]:
        """Check for common spelling/word choice errors"""
        issues = []
        suggestions = []

        common_errors = {
            r"\bthier\b": "their",
            r"\bteh\b": "the",
            r"\brecieve\b": "receive",
            r"\bseperate\b": "separate",
            r"\boccured\b": "occurred",
            r"\buntill\b": "until",
            r"\bwich\b": "which",
            r"\bthat's\b": "that is",  # For formal writing
            r"\bwon't\b": "will not",  # For formal writing
            r"\bcan't\b": "cannot",  # For formal writing
        }

        for pattern, correct in common_errors.items():
            if re.search(pattern, content, re.IGNORECASE):
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    issues.append(f"Possible error: '{match.group()}'")
                    suggestions.append(f"Did you mean '{correct}'?")

        return issues, suggestions

    def _check_consistency(self, content: str) -> tuple[list[str], list[str]]:
        """Check for consistency issues"""
        issues = []
        suggestions = []

        # Check for mixed British/American spelling
        british_american = [
            (r"\bcolour\b", r"\bcolor\b", "colour/color"),
            (r"\bfavourite\b", r"\bfavorite\b", "favourite/favorite"),
            (r"\borganise\b", r"\borganize\b", "organise/organize"),
            (r"\brealise\b", r"\brealize\b", "realise/realize"),
            (r"\bcentre\b", r"\bcenter\b", "centre/center"),
        ]

        for british, american, word_pair in british_american:
            has_british = bool(re.search(british, content, re.IGNORECASE))
            has_american = bool(re.search(american, content, re.IGNORECASE))

            if has_british and has_american:
                issues.append(f"Mixed spelling variants: {word_pair}")
                suggestions.append("Use consistent spelling throughout (British or American)")
                break  # Only report one instance

        # Check for number formatting consistency
        has_digits = bool(re.search(r"\b\d{1,2}\b", content))
        has_words = bool(re.search(r"\b(one|two|three|four|five|six|seven|eight|nine)\b", content, re.IGNORECASE))

        if has_digits and has_words:
            issues.append("Mixed number formatting (digits and words)")
            suggestions.append("Use consistent number formatting (typically words for 1-9, digits for 10+)")

        return issues, suggestions

    def _check_punctuation(self, content: str) -> tuple[list[str], list[str]]:
        """Check for punctuation issues"""
        issues = []
        suggestions = []

        # Check for double spaces
        if "  " in content:
            issues.append("Double spaces found")
            suggestions.append("Use single spaces between sentences")

        # Check for missing spaces after punctuation
        if re.search(r"[.!?,;:]\w", content):
            issues.append("Missing space after punctuation")
            suggestions.append("Add space after punctuation marks")

        # Check for multiple punctuation marks
        if re.search(r"[!?]{2,}", content):
            issues.append("Multiple punctuation marks")
            suggestions.append("Use single punctuation marks")

        return issues, suggestions

    def _calculate_style_score(
        self, issue_counts: dict[str, int]
    ) -> tuple[int, str]:
        """Calculate overall style score"""
        total_issues = sum(issue_counts.values())

        # Weight different issue types
        weighted_score = 100
        weighted_score -= issue_counts.get("passive_voice", 0) * 3
        weighted_score -= issue_counts.get("wordiness", 0) * 4
        weighted_score -= issue_counts.get("spelling", 0) * 5
        weighted_score -= issue_counts.get("consistency", 0) * 4
        weighted_score -= issue_counts.get("punctuation", 0) * 2
        weighted_score -= issue_counts.get("repetition", 0) * 3

        score = max(0, weighted_score)

        if score >= 90:
            level = "Excellent"
        elif score >= 80:
            level = "Good"
        elif score >= 70:
            level = "Fair"
        elif score >= 60:
            level = "Needs Improvement"
        else:
            level = "Poor"

        return score, level

    async def validate(self, content: str, metadata: dict[str, Any]) -> PluginResult:
        """Validate content grammar and style"""
        try:
            all_issues = []
            all_suggestions = []
            issue_counts = {}

            # Run checks
            checks = [
                ("passive_voice", self._check_passive_voice),
                ("repetition", self._check_sentence_starters),
                ("wordiness", self._check_wordiness),
                ("spelling", self._check_spelling_common_errors),
                ("consistency", self._check_consistency),
                ("punctuation", self._check_punctuation),
            ]

            for check_name, check_func in checks:
                issues, suggestions = check_func(content)
                issue_counts[check_name] = len(issues)
                all_issues.extend(issues)
                all_suggestions.extend(suggestions)

            # Calculate score
            score, level = self._calculate_style_score(issue_counts)

            # Determine pass/fail
            formal_writing = metadata.get("config", {}).get("formal", True)
            threshold = 70 if formal_writing else 60
            passed = score >= threshold

            if passed:
                message = f"Grammar and style check passed ({level})"
            else:
                message = f"Grammar and style issues detected ({level})"

            return PluginResult(
                success=passed,
                message=message,
                data={
                    "score": score,
                    "level": level,
                    "issue_counts": issue_counts,
                    "total_issues": len(all_issues),
                    "issues": all_issues[:10],  # Limit to first 10
                    "formal_writing": formal_writing,
                    "checks_performed": list(issue_counts.keys()),
                },
                suggestions=all_suggestions[:10] if all_suggestions else None,
            )

        except Exception as e:
            return PluginResult(
                success=False,
                message=f"Grammar validation failed: {e!s}",
            )
