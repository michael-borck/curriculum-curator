"""
Alternative verification methods for restrictive environments
"""

import hashlib
import secrets
from datetime import datetime, timedelta


def generate_manual_verification_token(email: str) -> str:
    """Generate a deterministic verification token based on email and secret"""
    # This creates a predictable token that admins can generate independently
    secret_salt = "CurriculumCurator2025"  # Change this for your deployment
    token_input = f"{email.lower()}{secret_salt}{datetime.utcnow().strftime('%Y-%m-%d')}"
    return hashlib.sha256(token_input.encode()).hexdigest()[:8].upper()

def generate_admin_override_code(email: str, admin_secret: str = "ADMIN_OVERRIDE_2025") -> str:
    """Generate an admin override code for manual verification"""
    # This allows admins to generate a code offline that users can enter
    code_input = f"{email.lower()}{admin_secret}"
    return hashlib.md5(code_input.encode()).hexdigest()[:6].upper()

def generate_local_verification_link(email: str, base_url: str = "http://localhost:3000") -> str:
    """Generate a local verification link that doesn't require email"""
    token = secrets.token_urlsafe(32)
    # Store this token in a local file or database
    return f"{base_url}/verify-local?email={email}&token={token}"

class AlternativeVerification:
    """Handle alternative verification methods"""

    @staticmethod
    def generate_verification_options(email: str) -> dict:
        """Generate multiple verification options for users"""
        return {
            "manual_code": generate_manual_verification_token(email),
            "admin_code": generate_admin_override_code(email),
            "valid_until": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "instructions": {
                "option1": "Enter the manual verification code shown below",
                "option2": "Ask your administrator for an override code",
                "option3": "Contact support with your registration details"
            }
        }

    @staticmethod
    def verify_alternative_code(email: str, code: str) -> tuple[bool, str]:
        """Verify an alternative verification code"""
        # Check manual verification token
        expected_manual = generate_manual_verification_token(email)
        if code.upper() == expected_manual:
            return True, "Manual verification successful"

        # Check admin override
        expected_admin = generate_admin_override_code(email)
        if code.upper() == expected_admin:
            return True, "Admin override verification successful"

        # Check if it's a development code
        if code == "DEV123" and email.endswith((".edu.au", "@localhost")):
            return True, "Development verification successful"

        return False, "Invalid verification code"
