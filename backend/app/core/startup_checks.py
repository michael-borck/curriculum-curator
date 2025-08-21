"""
Startup checks and database cleanup
"""

import logging

from pydantic import EmailStr, ValidationError
from sqlalchemy.orm import Session

from app.models import User

logger = logging.getLogger(__name__)


def validate_and_clean_emails(db: Session) -> None:
    """
    Check all user emails are valid and remove invalid ones.
    This prevents Pydantic validation errors at runtime.
    """
    try:
        users = db.query(User).all()
        invalid_users = []

        for user in users:
            try:
                # Test if email passes Pydantic validation
                # Simply create an EmailStr instance to validate
                EmailStr(user.email)
            except (ValidationError, ValueError, TypeError) as e:
                logger.warning(f"Invalid email found: {user.email} - {e}")
                invalid_users.append(user)

        # Remove users with invalid emails
        if invalid_users:
            for user in invalid_users:
                logger.info(f"Removing user with invalid email: {user.email}")
                db.delete(user)
            db.commit()
            logger.info(f"Cleaned {len(invalid_users)} users with invalid emails")

    except Exception:
        logger.exception("Error during email validation")
        db.rollback()


def run_startup_checks(db: Session) -> None:
    """
    Run all startup checks and cleanup tasks
    """
    logger.info("Running startup checks...")

    # DISABLED: Email validation was incorrectly removing valid users
    # The EmailStr validation was using the wrong method signature
    # and deleting users with valid emails like "211934g@curtin.edu.au"
    # validate_and_clean_emails(db)

    # Instead, just log the user count for monitoring
    user_count = db.query(User).count()
    logger.info(f"Current user count: {user_count}")

    logger.info("Startup checks completed")
