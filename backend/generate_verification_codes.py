#!/usr/bin/env python3
"""
Generate verification codes for users without email access
"""

import hashlib
import sys
from datetime import datetime


def generate_manual_code(email: str) -> str:
    """Generate today's manual verification code for an email"""
    secret_salt = "CurriculumCurator2025"
    today = datetime.utcnow().strftime('%Y-%m-%d')
    token_input = f"{email.lower()}{secret_salt}{today}"
    return hashlib.sha256(token_input.encode()).hexdigest()[:8].upper()


def generate_admin_override(email: str) -> str:
    """Generate permanent admin override code for an email"""
    admin_secret = "ADMIN_OVERRIDE_2025"
    code_input = f"{email.lower()}{admin_secret}"
    return hashlib.md5(code_input.encode()).hexdigest()[:6].upper()


def main():
    print("\n" + "="*60)
    print("VERIFICATION CODE GENERATOR")
    print("="*60)

    email = sys.argv[1] if len(sys.argv) > 1 else input("\nEnter user email: ").strip()

    if not email:
        print("❌ Email is required")
        return

    print(f"\n📧 Email: {email}")
    print("-"*40)

    # Generate codes
    manual_code = generate_manual_code(email)
    admin_code = generate_admin_override(email)

    print("\n🔑 VERIFICATION CODES:")
    print(f"   Daily Code (valid today):  {manual_code}")
    print(f"   Admin Override (permanent): {admin_code}")
    print("   Development Code:           DEV123")

    print("\n📝 INSTRUCTIONS:")
    print("   1. User can enter any of these codes on the verification page")
    print("   2. Daily code expires at midnight UTC")
    print("   3. Admin override code never expires")
    print("   4. DEV123 works for any .edu.au email")

    print("\n✅ Share the appropriate code with the user")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
