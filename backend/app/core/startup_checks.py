"""
Startup checks and database cleanup
"""

import logging
from sqlalchemy.orm import Session
from pydantic import EmailStr, ValidationError

logger = logging.getLogger(__name__)


def validate_and_clean_emails(db: Session) -> None:
    """
    Check all user emails are valid and remove invalid ones.
    This prevents Pydantic validation errors at runtime.
    """
    from app.models import User
    
    try:
        users = db.query(User).all()
        invalid_users = []
        
        for user in users:
            try:
                # Test if email passes Pydantic validation
                EmailStr._validate(user.email)
            except (ValidationError, ValueError) as e:
                logger.warning(f"Invalid email found: {user.email} - {e}")
                invalid_users.append(user)
        
        # Remove users with invalid emails
        if invalid_users:
            for user in invalid_users:
                logger.info(f"Removing user with invalid email: {user.email}")
                db.delete(user)
            db.commit()
            logger.info(f"Cleaned {len(invalid_users)} users with invalid emails")
        
    except Exception as e:
        logger.error(f"Error during email validation: {e}")
        db.rollback()


def run_startup_checks(db: Session) -> None:
    """
    Run all startup checks and cleanup tasks
    """
    logger.info("Running startup checks...")
    
    # Clean invalid emails
    validate_and_clean_emails(db)
    
    logger.info("Startup checks completed")