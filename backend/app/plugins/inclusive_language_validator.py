"""
Inclusive Language Validator Plugin.

Checks for non-inclusive, biased, or potentially offensive language
"""

import re
from typing import Any

from app.plugins.base import PluginResult, ValidatorPlugin


class InclusiveLanguageValidator(ValidatorPlugin):
    """Validates content for inclusive and unbiased language."""

    def __init__(self) -> None:
        """Initialize the validator with problematic terms."""
        super().__init__()

        # Terms to check with their suggestions
        # Format: "term": ("category", "suggestion")
        self._problematic_terms = {
            # Gender-specific terms
            "mankind": ("gender", "humankind, humanity, people"),
            "manpower": ("gender", "workforce, staff, personnel"),
            "chairman": ("gender", "chairperson, chair"),
            "policeman": ("gender", "police officer"),
            "fireman": ("gender", "firefighter"),
            "businessman": ("gender", "business person, entrepreneur"),
            "salesman": ("gender", "salesperson, sales representative"),
            "mailman": ("gender", "mail carrier, postal worker"),
            "freshman": ("gender", "first-year student"),
            "man-hours": ("gender", "person-hours, work hours"),
            "man-made": ("gender", "artificial, synthetic, human-made"),
            "guys": ("gender", "everyone, folks, team (context-dependent)"),
            # Ability-related terms
            "crazy": ("ability", "wild, amazing, unexpected"),
            "insane": ("ability", "incredible, unbelievable"),
            "dumb": ("ability", "unable to speak (only if medically accurate)"),
            "lame": ("ability", "boring, unimpressive"),
            "retarded": ("ability", "delayed, slow"),
            "crippled": ("ability", "disabled, has a disability"),
            "handicapped": ("ability", "person with a disability"),
            "normal people": ("ability", "typical people, people without disabilities"),
            "suffers from": ("ability", "has, lives with"),
            "wheelchair-bound": ("ability", "wheelchair user"),
            # Age-related terms
            "elderly": ("age", "older adults, seniors"),
            "youngster": ("age", "young person"),
            # Cultural/racial terms
            "minority": (
                "cultural",
                "underrepresented group (be specific when possible)",
            ),
            "exotic": ("cultural", "unique, distinctive"),
            "tribe": ("cultural", "group, team (unless referring to actual tribes)"),
            "ghetto": ("cultural", "neighborhood, community"),
            "third-world": ("cultural", "developing country, Global South"),
            "oriental": ("cultural", "Asian (be specific about region)"),
            # Technical/professional terms
            "master/slave": ("technical", "primary/replica, main/secondary"),
            "whitelist/blacklist": (
                "technical",
                "allowlist/blocklist, permitlist/denylist",
            ),
            "dummy": ("technical", "placeholder, sample, test"),
            "sanity check": ("technical", "validation check, consistency check"),
            # Violence-related metaphors
            "killing it": ("violence", "doing great, excelling"),
            "crush it": ("violence", "succeed, excel"),
            "beat": ("violence", "surpass, outperform"),
        }

        # Phrases that need context checking
        self._context_phrases = [
            (r"\bhe or she\b", "they (singular)", "gender"),
            (r"\bhis or her\b", "their", "gender"),
            (r"\bhe/she\b", "they", "gender"),
            (r"\bhis/her\b", "their", "gender"),
            (r"\bladies and gentlemen\b", "everyone, distinguished guests", "gender"),
            (r"\bmother tongue\b", "native language, first language", "cultural"),
            (
                r"\bforeign\s+(?:language|student|national)\b",
                "international, non-native",
                "cultural",
            ),
        ]

    @property
    def name(self) -> str:
        """Return plugin name."""
        return "inclusive_language_validator"

    @property
    def description(self) -> str:
        """Return plugin description."""
        return "Checks for inclusive, unbiased language"

    def _check_problematic_terms(self, content: str) -> tuple[list[str], list[str]]:
        """Check for problematic terms."""
        issues = []
        suggestions = []
        found_terms = {}

        content_lower = content.lower()

        for term in self._problematic_terms:
            # Use word boundaries to avoid false positives
            pattern = rf"\b{re.escape(term)}\b"
            matches = re.finditer(pattern, content_lower, re.IGNORECASE)

            for match in matches:
                if term not in found_terms:
                    found_terms[term] = []
                # Get surrounding context (20 chars before and after)
                start = max(0, match.start() - 20)
                end = min(len(content), match.end() + 20)
                context = content[start:end].strip()
                found_terms[term].append(context)

        # Generate issues and suggestions
        for term, contexts in found_terms.items():
            category, suggestion = self._problematic_terms[term]
            issue = f"[{category}] Found potentially problematic term: '{term}'"
            if len(contexts) == 1:
                issue += f" in context: '...{contexts[0]}...'"
            else:
                issue += f" ({len(contexts)} occurrences)"
            issues.append(issue)
            suggestions.append(f"Consider replacing '{term}' with: {suggestion}")

        return issues, suggestions

    def _check_context_phrases(self, content: str) -> tuple[list[str], list[str]]:
        """Check for phrases that need context consideration."""
        issues = []
        suggestions = []

        for pattern, suggestion, category in self._context_phrases:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            count = 0
            contexts = []

            for match in matches:
                count += 1
                # Get surrounding context
                start = max(0, match.start() - 20)
                end = min(len(content), match.end() + 20)
                context = content[start:end].strip()
                if len(contexts) < 3:  # Limit examples
                    contexts.append(context)

            if count > 0 and contexts:
                # Use the pattern itself if no match available
                contexts[0].strip() if contexts else pattern
                issue = f"[{category}] Found phrase that could be more inclusive"
                if count == 1:
                    issue += f" in: '...{contexts[0]}...'"
                else:
                    issue += f" ({count} occurrences)"
                issues.append(issue)
                suggestions.append(f"Consider using: {suggestion}")

        return issues, suggestions

    def _check_pronouns(self, content: str) -> tuple[list[str], list[str]]:
        """Check for exclusive pronoun usage."""
        issues = []
        suggestions = []

        # Check for generic "he" usage
        generic_he_pattern = r"\b(?:he|him|his)\b.*?\b(?:student|user|developer|person|individual|employee|teacher|learner)\b"
        if re.search(generic_he_pattern, content, re.IGNORECASE):
            issues.append("[gender] Generic masculine pronouns detected")
            suggestions.append(
                "Use 'they/them/their' for generic references or alternate pronouns"
            )

        # Check for assumption patterns
        assumption_patterns = [
            (
                r"assumes? (?:he|she) (?:has|knows|understands)",
                "Avoid assuming gender in examples",
            ),
        ]

        for pattern, suggestion in assumption_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append("[gender] Gender assumption detected")
                suggestions.append(suggestion)

        return issues, suggestions

    def _calculate_inclusivity_score(self, issue_counts: dict[str, int]) -> int:
        """Calculate inclusivity score based on issues found."""
        total_issues = sum(issue_counts.values())

        if total_issues == 0:
            return 100

        # Weight different categories
        weighted_score = 100
        weighted_score -= issue_counts.get("gender", 0) * 5
        weighted_score -= issue_counts.get("ability", 0) * 7
        weighted_score -= issue_counts.get("cultural", 0) * 6
        weighted_score -= issue_counts.get("technical", 0) * 3
        weighted_score -= issue_counts.get("age", 0) * 4
        weighted_score -= issue_counts.get("violence", 0) * 2

        return max(0, weighted_score)

    async def validate(self, content: str, metadata: dict[str, Any]) -> PluginResult:
        """Validate content for inclusive language."""
        try:
            all_issues = []
            all_suggestions = []
            issue_counts = {
                "gender": 0,
                "ability": 0,
                "cultural": 0,
                "technical": 0,
                "age": 0,
                "violence": 0,
            }

            # Run all checks
            checks = [
                self._check_problematic_terms,
                self._check_context_phrases,
                self._check_pronouns,
            ]

            for check_func in checks:
                issues, suggestions = check_func(content)
                all_issues.extend(issues)
                all_suggestions.extend(suggestions)

            # Count issues by category
            for issue in all_issues:
                for category in issue_counts:
                    if f"[{category}]" in issue:
                        issue_counts[category] += 1
                        break

            # Calculate score
            score = self._calculate_inclusivity_score(issue_counts)

            # Determine pass/fail
            strict_mode = metadata.get("config", {}).get("strict", False)
            threshold = 80 if strict_mode else 70
            passed = score >= threshold

            # Generate message
            if len(all_issues) == 0:
                message = "Content uses inclusive language"
            elif passed:
                message = f"Minor inclusivity improvements suggested (score: {score})"
            else:
                message = f"Multiple inclusivity issues found (score: {score})"

            return PluginResult(
                success=passed,
                message=message,
                data={
                    "score": score,
                    "total_issues": len(all_issues),
                    "issue_counts": issue_counts,
                    "issues": all_issues[:10],  # Limit to first 10
                    "categories_affected": [
                        k for k, v in issue_counts.items() if v > 0
                    ],
                },
                suggestions=all_suggestions[:10] if all_suggestions else None,
            )

        except Exception as e:
            return PluginResult(
                success=False,
                message=f"Inclusive language validation failed: {e!s}",
            )
