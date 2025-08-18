"""
Development configuration for bypassing email verification
"""


# Domains that bypass email verification in development
BYPASS_VERIFICATION_DOMAINS: list[str] = [
    "@curtin.edu.au",
    "@localhost",
    "@example.com",
]

# Magic verification code for development (only works for bypass domains)
DEV_VERIFICATION_CODE = "000000"

def should_bypass_verification(email: str) -> bool:
    """Check if email should bypass verification in development"""
    email_lower = email.lower()
    return any(email_lower.endswith(domain) for domain in BYPASS_VERIFICATION_DOMAINS)

def is_dev_verification_code(code: str) -> bool:
    """Check if this is the development verification code"""
    return code == DEV_VERIFICATION_CODE
