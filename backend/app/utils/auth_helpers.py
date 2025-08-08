"""
Authentication helper utilities
"""

import secrets
import string
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import EmailVerification, PasswordReset, User
from app.services.email_service import email_service


class AuthHelpers:
    """Helper functions for authentication processes"""

    @staticmethod
    def generate_verification_code(length: int = 6) -> str:
        """Generate a secure random verification code"""
        digits = string.digits
        return ''.join(secrets.choice(digits) for _ in range(length))

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a secure random token"""
        chars = string.ascii_letters + string.digits
        return ''.join(secrets.choice(chars) for _ in range(length))

    @staticmethod
    async def create_and_send_verification(
        db: Session,
        user: User,
        expires_minutes: int = 15
    ) -> tuple[bool, str | None]:
        """
        Create email verification record and send verification email
        Returns: (success, verification_code)
        """
        try:
            # Generate verification code
            verification_code = AuthHelpers.generate_verification_code()

            # Create verification record
            verification = EmailVerification(
                user_id=user.id,
                code=verification_code,
                expires_minutes=expires_minutes
            )

            db.add(verification)
            db.commit()

            # Send verification email
            email_sent = await email_service.send_verification_email(
                user, verification_code, expires_minutes
            )

            if email_sent:
                return True, verification_code
            # If email failed, remove the verification record
            db.delete(verification)
            db.commit()
            return False, None

        except Exception as e:
            db.rollback()
            print(f"❌ Failed to create verification for {user.email}: {e}")
            return False, None

    @staticmethod
    async def create_and_send_password_reset(
        db: Session,
        user: User,
        expires_minutes: int = 30
    ) -> tuple[bool, str | None]:
        """
        Create password reset record and send reset email
        Returns: (success, reset_code)
        """
        try:
            # Generate reset code
            reset_code = AuthHelpers.generate_verification_code()

            # Invalidate any existing password resets for this user
            existing_resets = db.query(PasswordReset).filter(
                PasswordReset.user_id == user.id,
                not PasswordReset.used
            ).all()

            for reset in existing_resets:
                reset.used = True

            # Create new password reset record
            password_reset = PasswordReset(
                user_id=user.id,
                token=reset_code,
                expires_minutes=expires_minutes
            )

            db.add(password_reset)
            db.commit()

            # Send reset email
            email_sent = await email_service.send_password_reset_email(
                user, reset_code, expires_minutes
            )

            if email_sent:
                return True, reset_code
            # If email failed, mark as used
            password_reset.used = True
            db.commit()
            return False, None

        except Exception as e:
            db.rollback()
            print(f"❌ Failed to create password reset for {user.email}: {e}")
            return False, None

    @staticmethod
    def verify_email_code(
        db: Session,
        email: str,
        code: str
    ) -> tuple[bool, User | None, str | None]:
        """
        Verify email verification code
        Returns: (success, user, error_message)
        """
        try:
            # Find user by email
            user = db.query(User).filter(User.email == email.lower().strip()).first()
            if not user:
                return False, None, "User not found"

            # Find valid verification code
            verification = db.query(EmailVerification).filter(
                EmailVerification.user_id == user.id,
                EmailVerification.code == code,
                not EmailVerification.used
            ).order_by(EmailVerification.created_at.desc()).first()

            if not verification:
                return False, None, "Invalid verification code"

            if verification.is_expired:
                return False, None, "Verification code has expired"

            # Mark verification as used and user as verified
            verification.mark_as_used()
            user.is_verified = True
            db.commit()

            return True, user, None

        except Exception as e:
            db.rollback()
            print(f"❌ Error verifying code for {email}: {e}")
            return False, None, "Verification failed"

    @staticmethod
    def verify_reset_code(
        db: Session,
        email: str,
        code: str
    ) -> tuple[bool, User | None, str | None]:
        """
        Verify password reset code
        Returns: (success, user, error_message)
        """
        try:
            # Find user by email
            user = db.query(User).filter(User.email == email.lower().strip()).first()
            if not user:
                return False, None, "User not found"

            # Find valid reset code
            reset = db.query(PasswordReset).filter(
                PasswordReset.user_id == user.id,
                PasswordReset.token == code,
                not PasswordReset.used
            ).order_by(PasswordReset.created_at.desc()).first()

            if not reset:
                return False, None, "Invalid reset code"

            if reset.is_expired:
                return False, None, "Reset code has expired"

            return True, user, None

        except Exception as e:
            print(f"❌ Error verifying reset code for {email}: {e}")
            return False, None, "Verification failed"

    @staticmethod
    def mark_reset_code_used(db: Session, email: str, code: str) -> bool:
        """Mark a password reset code as used"""
        try:
            user = db.query(User).filter(User.email == email.lower().strip()).first()
            if not user:
                return False

            reset = db.query(PasswordReset).filter(
                PasswordReset.user_id == user.id,
                PasswordReset.token == code,
                not PasswordReset.used
            ).first()

            if reset:
                reset.mark_as_used()
                db.commit()
                return True

            return False

        except Exception as e:
            db.rollback()
            print(f"❌ Error marking reset code as used: {e}")
            return False

    @staticmethod
    def clean_expired_codes(db: Session) -> tuple[int, int]:
        """
        Clean up expired verification and reset codes
        Returns: (expired_verifications_removed, expired_resets_removed)
        """
        try:
            current_time = datetime.utcnow()

            # Remove expired verifications
            expired_verifications = db.query(EmailVerification).filter(
                EmailVerification.expires_at < current_time
            ).all()

            for verification in expired_verifications:
                db.delete(verification)

            # Remove expired password resets
            expired_resets = db.query(PasswordReset).filter(
                PasswordReset.expires_at < current_time
            ).all()

            for reset in expired_resets:
                db.delete(reset)

            db.commit()

            ver_count = len(expired_verifications)
            reset_count = len(expired_resets)

            if ver_count > 0 or reset_count > 0:
                print(f"🧹 Cleaned up {ver_count} expired verifications and {reset_count} expired resets")

            return ver_count, reset_count

        except Exception as e:
            db.rollback()
            print(f"❌ Error cleaning expired codes: {e}")
            return 0, 0


# Convenience instance
auth_helpers = AuthHelpers()
