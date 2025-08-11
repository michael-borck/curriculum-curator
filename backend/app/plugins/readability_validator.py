"""
Readability Validator Plugin
Analyzes text readability using multiple metrics
"""

import re
from typing import Any

from app.plugins.base import PluginResult, ValidatorPlugin


class ReadabilityValidator(ValidatorPlugin):
    """Validates content readability using various metrics"""

    @property
    def name(self) -> str:
        return "readability_validator"

    @property
    def description(self) -> str:
        return "Analyzes text readability using Flesch-Kincaid and other metrics"

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (simplified algorithm)"""
        word = word.lower()
        vowels = "aeiouy"
        syllable_count = 0
        previous_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel

        # Adjust for silent e
        if word.endswith("e"):
            syllable_count -= 1

        # Ensure at least 1 syllable
        return max(1, syllable_count)

    def _analyze_text(self, text: str) -> dict[str, Any]:
        """Analyze text and return metrics"""
        # Clean text
        text = re.sub(r"[#*`]", "", text)  # Remove markdown formatting
        text = re.sub(r"\n+", " ", text)  # Replace newlines with spaces
        text = re.sub(r"\s+", " ", text)  # Normalize whitespace

        # Split into sentences
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = len(sentences)

        # Split into words
        words = text.split()
        words = [w.strip(".,!?;:\"'") for w in words]
        words = [w for w in words if w]
        word_count = len(words)

        # Count syllables
        total_syllables = sum(self._count_syllables(word) for word in words)

        # Count complex words (3+ syllables)
        complex_words = sum(1 for word in words if self._count_syllables(word) >= 3)

        return {
            "sentence_count": sentence_count,
            "word_count": word_count,
            "syllable_count": total_syllables,
            "complex_word_count": complex_words,
            "avg_words_per_sentence": word_count / max(sentence_count, 1),
            "avg_syllables_per_word": total_syllables / max(word_count, 1),
        }

    def _calculate_flesch_reading_ease(self, metrics: dict[str, Any]) -> float:
        """
        Calculate Flesch Reading Ease score
        Score interpretation:
        90-100: Very Easy (5th grade)
        80-90: Easy (6th grade)
        70-80: Fairly Easy (7th grade)
        60-70: Standard (8th-9th grade)
        50-60: Fairly Difficult (10th-12th grade)
        30-50: Difficult (College)
        0-30: Very Difficult (College graduate)
        """
        if metrics["word_count"] == 0:
            return 100.0

        score = (
            206.835
            - 1.015 * metrics["avg_words_per_sentence"]
            - 84.6 * metrics["avg_syllables_per_word"]
        )
        return max(0, min(100, score))

    def _calculate_flesch_kincaid_grade(self, metrics: dict[str, Any]) -> float:
        """Calculate Flesch-Kincaid Grade Level"""
        if metrics["word_count"] == 0:
            return 0.0

        grade = (
            0.39 * metrics["avg_words_per_sentence"]
            + 11.8 * metrics["avg_syllables_per_word"]
            - 15.59
        )
        return max(0, grade)

    def _calculate_gunning_fog(self, metrics: dict[str, Any]) -> float:
        """Calculate Gunning Fog Index"""
        if metrics["word_count"] == 0:
            return 0.0

        fog = 0.4 * (
            metrics["avg_words_per_sentence"]
            + 100 * (metrics["complex_word_count"] / metrics["word_count"])
        )
        return fog

    def _get_readability_level(self, flesch_ease: float) -> str:
        """Get readability level description"""
        if flesch_ease >= 90:
            return "Very Easy (5th grade)"
        if flesch_ease >= 80:
            return "Easy (6th grade)"
        if flesch_ease >= 70:
            return "Fairly Easy (7th grade)"
        if flesch_ease >= 60:
            return "Standard (8th-9th grade)"
        if flesch_ease >= 50:
            return "Fairly Difficult (10th-12th grade)"
        if flesch_ease >= 30:
            return "Difficult (College)"
        return "Very Difficult (College graduate)"

    def _generate_suggestions(
        self, metrics: dict[str, Any], target_level: str
    ) -> list[str]:
        """Generate improvement suggestions based on metrics"""
        suggestions = []

        # Get target levels from metadata
        target_grade = 12  # Default to high school
        if target_level == "elementary":
            target_grade = 5
        elif target_level == "middle_school":
            target_grade = 8
        elif target_level == "high_school":
            target_grade = 12
        elif target_level == "university":
            target_grade = 14

        current_grade = metrics["flesch_kincaid_grade"]

        # Sentence length suggestions
        if metrics["avg_words_per_sentence"] > 20:
            suggestions.append(
                f"Sentences are too long (avg {metrics['avg_words_per_sentence']:.1f} words). "
                + "Consider breaking complex sentences into shorter ones (aim for 15-20 words)."
            )
        elif metrics["avg_words_per_sentence"] < 10:
            suggestions.append(
                f"Sentences are very short (avg {metrics['avg_words_per_sentence']:.1f} words). "
                + "Consider combining related ideas for better flow."
            )

        # Grade level suggestions
        if current_grade > target_grade + 2:
            suggestions.append(
                f"Content is too complex (grade {current_grade:.1f} vs target {target_grade}). "
                + "Simplify vocabulary and sentence structure."
            )
        elif current_grade < target_grade - 2:
            suggestions.append(
                f"Content may be too simple (grade {current_grade:.1f} vs target {target_grade}). "
                + "Consider adding more sophisticated vocabulary and concepts."
            )

        # Complex word suggestions
        complex_percentage = (
            metrics["complex_word_count"] / max(metrics["word_count"], 1) * 100
        )
        if complex_percentage > 20:
            suggestions.append(
                f"High proportion of complex words ({complex_percentage:.1f}%). "
                + "Consider using simpler alternatives where possible."
            )

        # Specific problem patterns
        if metrics["avg_syllables_per_word"] > 2:
            suggestions.append(
                "Words are generally complex. Use shorter, more common words where appropriate."
            )

        return suggestions

    async def validate(self, content: str, metadata: dict[str, Any]) -> PluginResult:
        """Validate content readability"""
        try:
            # Skip if content is too short
            if len(content) < 100:
                return PluginResult(
                    success=True,
                    message="Content too short for readability analysis",
                    data={"skipped": True},
                )

            # Analyze text
            metrics = self._analyze_text(content)

            # Calculate readability scores
            flesch_ease = self._calculate_flesch_reading_ease(metrics)
            flesch_kincaid_grade = self._calculate_flesch_kincaid_grade(metrics)
            gunning_fog = self._calculate_gunning_fog(metrics)

            # Get target level from metadata
            target_level = metadata.get("config", {}).get("target_level", "high_school")
            difficulty_level = metadata.get("difficulty_level", "intermediate")

            # Generate suggestions
            suggestions = self._generate_suggestions(
                {**metrics, "flesch_kincaid_grade": flesch_kincaid_grade},
                target_level,
            )

            # Determine if content passes validation
            passed = True
            message = f"Readability: {self._get_readability_level(flesch_ease)}"

            # Check against thresholds
            if target_level == "elementary" and flesch_kincaid_grade > 6:
                passed = False
                message = f"Content too complex for elementary level (Grade {flesch_kincaid_grade:.1f})"
            elif target_level == "middle_school" and flesch_kincaid_grade > 9:
                passed = False
                message = f"Content too complex for middle school (Grade {flesch_kincaid_grade:.1f})"
            elif target_level == "high_school" and flesch_kincaid_grade > 12:
                passed = False
                message = f"Content too complex for high school (Grade {flesch_kincaid_grade:.1f})"

            return PluginResult(
                success=passed,
                message=message,
                data={
                    "flesch_reading_ease": round(flesch_ease, 2),
                    "flesch_kincaid_grade": round(flesch_kincaid_grade, 1),
                    "gunning_fog_index": round(gunning_fog, 1),
                    "readability_level": self._get_readability_level(flesch_ease),
                    "metrics": metrics,
                    "target_level": target_level,
                },
                suggestions=suggestions if suggestions else None,
            )

        except Exception as e:
            return PluginResult(
                success=False,
                message=f"Readability analysis failed: {e!s}",
            )
