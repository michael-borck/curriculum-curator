"""
Spell Checker Plugin
Checks for spelling errors using pyspellchecker
"""

import re
from typing import Any

from app.plugins.base import PluginResult, ValidatorPlugin

# Try to import spellchecker - it's optional
try:
    from spellchecker import SpellChecker as PySpellChecker
    has_spellchecker = True
except ImportError:
    PySpellChecker = None
    has_spellchecker = False


class SpellChecker(ValidatorPlugin):
    """Checks content for spelling errors"""

    def __init__(self):
        super().__init__()
        self._spell_checker = None
        self._technical_terms = {
            # Programming terms
            "api",
            "apis",
            "backend",
            "frontend",
            "database",
            "sql",
            "nosql",
            "json",
            "xml",
            "yaml",
            "html",
            "css",
            "javascript",
            "typescript",
            "python",
            "java",
            "cpp",
            "csharp",
            "golang",
            "rust",
            "kotlin",
            "docker",
            "kubernetes",
            "microservices",
            "serverless",
            "webhook",
            "async",
            "await",
            "callback",
            "promise",
            "observable",
            "middleware",
            "orm",
            "crud",
            "rest",
            "graphql",
            "grpc",
            "websocket",
            "jwt",
            "oauth",
            "saml",
            "ldap",
            "cors",
            "csrf",
            "xss",
            "redis",
            "mongodb",
            "postgresql",
            "mysql",
            "elasticsearch",
            "github",
            "gitlab",
            "bitbucket",
            "git",
            "svn",
            "merge",
            "rebase",
            "ci",
            "cd",
            "devops",
            "agile",
            "scrum",
            "kanban",
            "jira",
            "npm",
            "pip",
            "maven",
            "gradle",
            "webpack",
            "vite",
            "babel",
            "react",
            "vue",
            "angular",
            "svelte",
            "nextjs",
            "nuxt",
            "gatsby",
            "django",
            "flask",
            "fastapi",
            "express",
            "nestjs",
            "spring",
            "tensorflow",
            "pytorch",
            "sklearn",
            "pandas",
            "numpy",
            "scipy",
            "jupyter",
            "colab",
            "anaconda",
            "conda",
            "virtualenv",
            "venv",
            # Educational terms
            "lms",
            "mooc",
            "elearning",
            "pedagogy",
            "andragogy",
            "curriculum",
            "syllabus",
            "rubric",
            "assessment",
            "formative",
            "summative",
            "bloom",
            "taxonomy",
            "constructivist",
            "behaviorist",
            "cognitivist",
            "scaffolding",
            "differentiation",
            "gamification",
            "microlearning",
            "asynchronous",
            "synchronous",
            "blended",
            "flipped",
            "hybrid",
            # Common tech abbreviations
            "http",
            "https",
            "url",
            "uri",
            "cdn",
            "dns",
            "ssl",
            "tls",
            "cpu",
            "gpu",
            "ram",
            "ssd",
            "hdd",
            "lan",
            "wan",
            "vpn",
            "ui",
            "ux",
            "gui",
            "cli",
            "ide",
            "sdk",
            "saas",
            "paas",
            "iaas",
            "aws",
            "gcp",
            "azure",
            "ec2",
            "s3",
            "lambda",
            "rds",
        }

    @property
    def name(self) -> str:
        return "spell_checker"

    @property
    def description(self) -> str:
        return "Checks for spelling errors with technical term awareness"

    def _get_spell_checker(self):
        """Lazy load spell checker"""
        if self._spell_checker is None:
            if has_spellchecker and PySpellChecker:
                self._spell_checker = PySpellChecker()
                # Add technical terms to dictionary
                self._spell_checker.word_frequency.load_words(self._technical_terms)
            else:
                # Fallback to basic checking if pyspellchecker not available
                self._spell_checker = "basic"
        return self._spell_checker

    def _extract_words(self, content: str) -> list[str]:
        """Extract words from content, excluding code blocks and URLs"""
        # Remove code blocks
        content = re.sub(r"```[\s\S]*?```", "", content)
        content = re.sub(r"`[^`]+`", "", content)

        # Remove URLs
        content = re.sub(r"https?://[^\s]+", "", content)
        content = re.sub(r"www\.[^\s]+", "", content)

        # Remove email addresses
        content = re.sub(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "", content
        )

        # Remove markdown formatting
        content = re.sub(r"[#*_\[\]()]", " ", content)

        # Extract words (letters only, no numbers or special chars)
        return re.findall(r"\b[a-zA-Z]+(?:'[a-zA-Z]+)?\b", content)

    def _basic_spell_check(self, words: list[str]) -> tuple[list[str], list[str]]:
        """Basic spell checking without external library"""
        issues = []
        suggestions = []

        # Common misspellings
        common_errors = {
            "recieve": "receive",
            "seperate": "separate",
            "occured": "occurred",
            "untill": "until",
            "wich": "which",
            "teh": "the",
            "thier": "their",
            "definately": "definitely",
            "accomodate": "accommodate",
            "acheive": "achieve",
            "accross": "across",
            "agressive": "aggressive",
            "apparant": "apparent",
            "arguement": "argument",
            "begining": "beginning",
            "beleive": "believe",
            "calender": "calendar",
            "collegue": "colleague",
            "comming": "coming",
            "commitee": "committee",
            "concious": "conscious",
            "decieve": "deceive",
            "dependant": "dependent",
            "desireable": "desirable",
            "dilemna": "dilemma",
            "disappoint": "disappoint",
            "ecstacy": "ecstasy",
            "embarass": "embarrass",
            "enviroment": "environment",
            "existance": "existence",
            "experiance": "experience",
            "foriegn": "foreign",
            "fourty": "forty",
            "foward": "forward",
            "freind": "friend",
            "goverment": "government",
            "grammer": "grammar",
            "harrass": "harass",
            "independant": "independent",
            "judgement": "judgment",
            "knowlege": "knowledge",
            "liason": "liaison",
            "libary": "library",
            "lisence": "license",
            "maintainance": "maintenance",
            "managable": "manageable",
            "millenia": "millennia",
            "mispell": "misspell",
            "neccessary": "necessary",
            "noticable": "noticeable",
            "occassion": "occasion",
            "occurence": "occurrence",
            "pavillion": "pavilion",
            "persistant": "persistent",
            "posession": "possession",
            "prefered": "preferred",
            "privelege": "privilege",
            "pronounciation": "pronunciation",
            "publically": "publicly",
            "realy": "really",
            "reccomend": "recommend",
            "refered": "referred",
            "rythm": "rhythm",
            "sieze": "seize",
            "supercede": "supersede",
            "suprise": "surprise",
            "tendancy": "tendency",
            "tommorrow": "tomorrow",
            "twelth": "twelfth",
            "underate": "underrate",
            "unfortunatly": "unfortunately",
            "upholstery": "upholstery",
            "useable": "usable",
            "vaccuum": "vacuum",
            "vegeterian": "vegetarian",
            "vehical": "vehicle",
            "visable": "visible",
            "wether": "whether",
            "whereever": "wherever",
        }

        checked_words = set()
        for word in words:
            word_lower = word.lower()
            if word_lower in checked_words:
                continue
            checked_words.add(word_lower)

            if word_lower in common_errors:
                issues.append(f"Misspelled word: '{word}'")
                suggestions.append(
                    f"Replace '{word}' with '{common_errors[word_lower]}'"
                )

        return issues[:20], suggestions[:20]  # Limit to 20

    def _advanced_spell_check(
        self, words: list[str], spell_checker
    ) -> tuple[list[str], list[str]]:
        """Advanced spell checking using pyspellchecker"""
        issues = []
        suggestions = []

        # Filter out technical terms and common words
        words_to_check = []
        for word in words:
            word_lower = word.lower()
            # Skip if it's a known technical term or very short word (likely abbreviations)
            if word_lower not in self._technical_terms and len(word) > 2:
                # Skip words with mixed case in middle (likely camelCase)
                if (
                    not (word[0].isupper() and word[1:].islower())
                    and not word.islower()
                ):
                    continue
                words_to_check.append(word)

        # Find misspelled words
        misspelled = spell_checker.unknown(words_to_check)

        for word in misspelled:
            # Get suggestions
            corrections = spell_checker.candidates(word)
            if corrections:
                # Filter out the original word and limit suggestions
                corrections = [c for c in corrections if c != word][:3]
                if corrections:
                    issues.append(f"Possible misspelling: '{word}'")
                    if len(corrections) == 1:
                        suggestions.append(f"Did you mean '{corrections[0]}'?")
                    else:
                        suggestions.append(
                            f"Did you mean one of: {', '.join(corrections)}?"
                        )

        return issues[:20], suggestions[:20]  # Limit to 20

    async def validate(self, content: str, metadata: dict[str, Any]) -> PluginResult:
        """Validate content for spelling errors"""
        try:
            # Extract words from content
            words = self._extract_words(content)

            if not words:
                return PluginResult(
                    success=True,
                    message="No text content to check",
                    data={"word_count": 0, "skipped": True},
                )

            # Get spell checker
            spell_checker = self._get_spell_checker()

            # Perform spell check
            if spell_checker == "basic":
                issues, suggestions = self._basic_spell_check(words)
            else:
                issues, suggestions = self._advanced_spell_check(words, spell_checker)

            # Calculate score
            error_rate = len(issues) / max(len({w.lower() for w in words}), 1)
            score = max(0, 100 - (error_rate * 500))  # 5 points per 1% error rate

            # Determine pass/fail
            threshold = metadata.get("config", {}).get("threshold", 90)
            passed = score >= threshold

            if passed:
                if issues:
                    message = (
                        f"Spell check passed with minor issues (score: {score:.0f})"
                    )
                else:
                    message = "No spelling errors detected"
            else:
                message = f"Multiple spelling errors found (score: {score:.0f})"

            return PluginResult(
                success=passed,
                message=message,
                data={
                    "score": round(score, 2),
                    "word_count": len(words),
                    "unique_words": len({w.lower() for w in words}),
                    "error_count": len(issues),
                    "error_rate": round(error_rate * 100, 2),
                    "issues": issues,
                    "spell_checker": "pyspellchecker"
                    if spell_checker != "basic"
                    else "basic",
                },
                suggestions=suggestions if suggestions else None,
            )

        except Exception as e:
            return PluginResult(
                success=False,
                message=f"Spell check failed: {e!s}",
            )
