"""
Enhanced password validation with security requirements
"""

import re

# Common weak passwords list (subset - in production, load from file)
COMMON_PASSWORDS = {
    "123456", "password", "123456789", "12345678", "12345", "1234567",
    "qwerty", "abc123", "password123", "admin", "letmein", "welcome",
    "monkey", "1234567890", "dragon", "iloveyou", "princess", "sunshine",
    "master", "123123", "football", "baseball", "superman", "computer",
    "michael", "jordan", "matrix", "money", "freedom", "hello", "batman",
    "trustno1", "hunter", "ranger", "buster", "thomas", "tigger",
    "robert", "access", "love", "internet", "service", "cookie", "test",
    "guest", "honda", "shadow", "mustang", "secret", "summer", "spider",
    "michelle", "whatever", "chicken", "startrek", "orange", "mercedes",
}


class PasswordValidator:
    """Enhanced password validator with comprehensive security checks"""

    # Configuration
    min_length = 8
    require_uppercase = True
    require_lowercase = True
    require_numbers = True
    require_special = True
    prevent_common_passwords = True
    prevent_personal_info = True
    max_repeated_chars = 3
    min_unique_chars = 8

    # Special characters
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    @classmethod
    def validate_password(  # noqa: PLR0912
        cls,
        password: str,
        user_name: str = "",
        user_email: str = ""
    ) -> tuple[bool, list[str]]:
        """
        Validate password against all security requirements

        Args:
            password: The password to validate
            user_name: User's name for personal info check
            user_email: User's email for personal info check

        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_errors)
        """
        errors = []

        # Basic length check
        if len(password) < cls.min_length:
            errors.append(f"Password must be at least {cls.min_length} characters long")

        # Character type requirements
        if cls.require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")

        if cls.require_lowercase and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")

        if cls.require_numbers and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")

        if cls.require_special and not any(c in cls.special_chars for c in password):
            errors.append(f"Password must contain at least one special character: {cls.special_chars}")

        # Common password check
        if cls.prevent_common_passwords:
            password_lower = password.lower()
            if password_lower in COMMON_PASSWORDS:
                errors.append("Password is too common. Please choose a more unique password")

            # Check for common patterns
            if cls._is_common_pattern(password):
                errors.append("Password follows a common pattern. Please choose a more complex password")

        # Personal information check
        if cls.prevent_personal_info:
            personal_errors = cls._check_personal_info(password, user_name, user_email)
            errors.extend(personal_errors)

        # Character diversity checks
        if len(set(password)) < cls.min_unique_chars:
            errors.append(f"Password must contain at least {cls.min_unique_chars} unique characters")

        # Repeated character check
        if cls._has_excessive_repeats(password):
            errors.append(f"Password cannot have more than {cls.max_repeated_chars} consecutive identical characters")

        # Keyboard pattern check
        if cls._has_keyboard_pattern(password):
            errors.append("Password cannot contain keyboard patterns (e.g., qwerty, asdf)")

        # Sequential pattern check
        if cls._has_sequential_pattern(password):
            errors.append("Password cannot contain sequential patterns (e.g., 123456, abcdef)")

        return len(errors) == 0, errors

    @classmethod
    def _is_common_pattern(cls, password: str) -> bool:
        """Check for common password patterns"""
        password_lower = password.lower()

        # Check for years (1900-2099)
        if re.search(r'(19|20)\d{2}', password):
            return True

        # Check for simple substitutions (@ for a, 3 for e, etc.)
        common_subs = str.maketrans('aeilost', '@3!10$7')
        transformed = password_lower.translate(common_subs)
        if transformed in COMMON_PASSWORDS:
            return True

        # Check for passwords with numbers/symbols just at the end
        if re.match(r'^[a-zA-Z]+[0-9!@#$%^&*()_+\-=\[\]{}|;:,.<>?]+$', password):
            word_part = re.match(r'^[a-zA-Z]+', password_lower).group()
            if len(word_part) >= 4 and word_part in COMMON_PASSWORDS:
                return True

        return False

    @classmethod
    def _check_personal_info(cls, password: str, user_name: str, user_email: str) -> list[str]:
        """Check if password contains personal information"""
        errors = []
        password_lower = password.lower()

        # Check name components
        if user_name:
            name_parts = user_name.lower().split()
            for part in name_parts:
                if len(part) >= 3 and part in password_lower:
                    errors.append("Password cannot contain parts of your name")
                    break

        # Check email components
        if user_email:
            email_user = user_email.split('@')[0].lower()
            if len(email_user) >= 3 and email_user in password_lower:
                errors.append("Password cannot contain parts of your email address")

            # Check domain name (without TLD)
            if '@' in user_email:
                domain = user_email.split('@')[1].split('.')[0].lower()
                if len(domain) >= 3 and domain in password_lower:
                    errors.append("Password cannot contain your email domain")

        return errors

    @classmethod
    def _has_excessive_repeats(cls, password: str) -> bool:
        """Check for excessive repeated characters"""
        count = 1
        for i in range(1, len(password)):
            if password[i] == password[i-1]:
                count += 1
                if count > cls.max_repeated_chars:
                    return True
            else:
                count = 1
        return False

    @classmethod
    def _has_keyboard_pattern(cls, password: str) -> bool:
        """Check for keyboard patterns"""
        keyboard_rows = [
            "qwertyuiop",
            "asdfghjkl",
            "zxcvbnm",
            "1234567890",
            "!@#$%^&*()"
        ]

        password_lower = password.lower()

        for row in keyboard_rows:
            # Check forward and backward patterns
            for direction in [row, row[::-1]]:
                for i in range(len(direction) - 3):  # Minimum 4 character pattern
                    pattern = direction[i:i+4]
                    if pattern in password_lower:
                        return True

        return False

    @classmethod
    def _has_sequential_pattern(cls, password: str) -> bool:
        """Check for sequential character patterns"""
        # Check for ascending/descending sequences
        for i in range(len(password) - 3):  # Minimum 4 character sequence
            substr = password[i:i+4]

            # Check numeric sequences
            if substr.isdigit():
                digits = [int(c) for c in substr]
                if cls._is_sequence(digits):
                    return True

            # Check alphabetic sequences
            elif substr.isalpha():
                ascii_vals = [ord(c.lower()) for c in substr]
                if cls._is_sequence(ascii_vals):
                    return True

        return False

    @classmethod
    def _is_sequence(cls, values: list[int]) -> bool:
        """Check if values form an ascending or descending sequence"""
        if len(values) < 4:
            return False

        # Check ascending
        ascending = all(values[i] == values[0] + i for i in range(len(values)))

        # Check descending
        descending = all(values[i] == values[0] - i for i in range(len(values)))

        return ascending or descending

    @classmethod
    def get_password_strength_score(cls, password: str) -> tuple[int, str]:
        """
        Calculate password strength score (0-100)

        Returns:
            Tuple[int, str]: (score, strength_description)
        """
        score = 0

        # Length bonus (up to 25 points)
        score += min(25, len(password) * 2)

        # Character variety (up to 25 points)
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in cls.special_chars for c in password)

        char_types = sum([has_lower, has_upper, has_digit, has_special])
        score += char_types * 6  # Up to 24 points

        # Uniqueness bonus (up to 20 points)
        unique_chars = len(set(password))
        score += min(20, unique_chars * 2)

        # Pattern penalties
        if cls._is_common_pattern(password):
            score -= 20
        if cls._has_keyboard_pattern(password):
            score -= 15
        if cls._has_sequential_pattern(password):
            score -= 15
        if cls._has_excessive_repeats(password):
            score -= 10

        # Common password penalty
        if password.lower() in COMMON_PASSWORDS:
            score -= 30

        score = max(0, min(100, score))

        # Strength descriptions
        if score >= 80:
            strength = "Very Strong"
        elif score >= 60:
            strength = "Strong"
        elif score >= 40:
            strength = "Moderate"
        elif score >= 20:
            strength = "Weak"
        else:
            strength = "Very Weak"

        return score, strength

    @classmethod
    def suggest_improvements(cls, password: str, errors: list[str]) -> list[str]:
        """Suggest specific improvements for password"""
        suggestions = []

        if len(password) < cls.min_length:
            needed = cls.min_length - len(password)
            suggestions.append(f"Add {needed} more characters")

        if not any(c.isupper() for c in password):
            suggestions.append("Add uppercase letters (A-Z)")

        if not any(c.islower() for c in password):
            suggestions.append("Add lowercase letters (a-z)")

        if not any(c.isdigit() for c in password):
            suggestions.append("Add numbers (0-9)")

        if not any(c in cls.special_chars for c in password):
            suggestions.append("Add special characters (!@#$%^&*)")

        if "common" in " ".join(errors).lower():
            suggestions.append("Use a more unique combination of words or phrases")

        if "personal" in " ".join(errors).lower():
            suggestions.append("Avoid using personal information like names or email parts")

        return suggestions
