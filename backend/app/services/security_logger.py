"""
Security logging service for centralized security event logging
"""

import time

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.security_log import SecurityEventType, SecurityLog
from app.models.user import User


class SecurityLogger:
    """Centralized security event logging service"""

    @staticmethod
    def log_authentication_event(
        db: Session,
        event_type: SecurityEventType,
        request: Request,
        user: User | None = None,
        success: bool = False,
        description: str | None = None,
        details: dict | None = None,
        response_time_ms: int | None = None,
    ) -> SecurityLog:
        """Log authentication-related security events"""

        # Determine severity based on event type
        severity = "info"
        if event_type in [
            SecurityEventType.LOGIN_FAILED,
            SecurityEventType.ACCOUNT_LOCKED,
            SecurityEventType.BRUTE_FORCE_DETECTED,
        ]:
            severity = "warning"
        elif event_type == SecurityEventType.SUSPICIOUS_ACTIVITY:
            severity = "error"

        return SecurityLog.log_event(
            db_session=db,
            event_type=event_type,
            ip_address=SecurityLogger._get_client_ip(request),
            user_id=str(user.id) if user else None,
            user_email=user.email if user else None,
            user_role=user.role if user else None,
            user_agent=SecurityLogger._get_user_agent(request),
            request_path=str(request.url.path),
            request_method=request.method,
            event_description=description,
            severity=severity,
            success="success" if success else "failure",
            details=details,
            response_time_ms=response_time_ms,
        )

    @staticmethod
    def log_security_event(
        db: Session,
        event_type: SecurityEventType,
        request: Request,
        severity: str = "warning",
        user: User | None = None,
        description: str | None = None,
        details: dict | None = None,
        response_time_ms: int | None = None,
    ) -> SecurityLog:
        """Log general security events (CSRF, rate limiting, etc.)"""

        return SecurityLog.log_event(
            db_session=db,
            event_type=event_type,
            ip_address=SecurityLogger._get_client_ip(request),
            user_id=str(user.id) if user else None,
            user_email=user.email if user else None,
            user_role=user.role if user else None,
            user_agent=SecurityLogger._get_user_agent(request),
            request_path=str(request.url.path),
            request_method=request.method,
            event_description=description,
            severity=severity,
            success="blocked",  # Security events typically represent blocked actions
            details=details,
            response_time_ms=response_time_ms,
        )

    @staticmethod
    def log_data_access_event(
        db: Session,
        event_type: SecurityEventType,
        request: Request,
        user: User,
        resource_type: str | None = None,
        resource_id: str | None = None,
        action: str | None = None,
        success: bool = True,
        details: dict | None = None,
        response_time_ms: int | None = None,
    ) -> SecurityLog:
        """Log data access and modification events"""

        # Build details dictionary
        event_details = details or {}
        if resource_type:
            event_details["resource_type"] = resource_type
        if resource_id:
            event_details["resource_id"] = resource_id
        if action:
            event_details["action"] = action

        severity = "info"
        if event_type in [
            SecurityEventType.DATA_DELETION,
            SecurityEventType.SENSITIVE_DATA_ACCESS,
        ]:
            severity = "warning"

        return SecurityLog.log_event(
            db_session=db,
            event_type=event_type,
            ip_address=SecurityLogger._get_client_ip(request),
            user_id=str(user.id),
            user_email=user.email,
            user_role=user.role,
            user_agent=SecurityLogger._get_user_agent(request),
            request_path=str(request.url.path),
            request_method=request.method,
            event_description=f"{action or 'Access'} {resource_type or 'resource'}" if resource_type else None,
            severity=severity,
            success="success" if success else "failure",
            details=event_details,
            response_time_ms=response_time_ms,
        )

    @staticmethod
    def log_admin_action(
        db: Session,
        request: Request,
        admin_user: User,
        action: str,
        target_user: User | None = None,
        details: dict | None = None,
        response_time_ms: int | None = None,
    ) -> SecurityLog:
        """Log administrative actions"""

        event_details = details or {}
        event_details["admin_action"] = action

        if target_user:
            event_details["target_user_id"] = str(target_user.id)
            event_details["target_user_email"] = target_user.email

        description = f"Admin action: {action}"
        if target_user:
            description += f" (target: {target_user.email})"

        return SecurityLog.log_event(
            db_session=db,
            event_type=SecurityEventType.ADMIN_ACTION,
            ip_address=SecurityLogger._get_client_ip(request),
            user_id=str(admin_user.id),
            user_email=admin_user.email,
            user_role=admin_user.role,
            user_agent=SecurityLogger._get_user_agent(request),
            request_path=str(request.url.path),
            request_method=request.method,
            event_description=description,
            severity="warning",  # Admin actions should be tracked carefully
            success="success",
            details=event_details,
            response_time_ms=response_time_ms,
        )

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded IP (behind proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fall back to direct connection IP
        return request.client.host if request.client else "unknown"

    @staticmethod
    def _get_user_agent(request: Request) -> str:
        """Extract user agent from request"""
        return request.headers.get("User-Agent", "Unknown")[:500]  # Truncate to fit DB field


# Decorators for automatic security logging
def log_security_event(event_type: SecurityEventType, severity: str = "warning"):
    """Decorator to automatically log security events"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            request = None
            db = None
            start_time = time.time()

            # Extract request and db from function arguments
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                elif hasattr(arg, 'query'):  # SQLAlchemy session
                    db = arg

            # Look in kwargs as well
            if not request:
                request = kwargs.get('request')
            if not db:
                db = kwargs.get('db')

            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Log the security event
                if request and db:
                    response_time = int((time.time() - start_time) * 1000)
                    SecurityLogger.log_security_event(
                        db=db,
                        event_type=event_type,
                        request=request,
                        severity=severity,
                        description=f"Security event in {func.__name__}: {str(e)[:200]}",
                        details={"function": func.__name__, "error": str(e)},
                        response_time_ms=response_time,
                    )
                raise
        return wrapper
    return decorator


def log_authentication_event(event_type: SecurityEventType):
    """Decorator to automatically log authentication events"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            request = None
            db = None
            start_time = time.time()

            # Extract request and db from function arguments
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                elif hasattr(arg, 'query'):  # SQLAlchemy session
                    db = arg

            # Look in kwargs as well
            if not request:
                request = kwargs.get('request')
            if not db:
                db = kwargs.get('db')

            try:
                result = await func(*args, **kwargs)

                # Log successful authentication event
                if request and db:
                    response_time = int((time.time() - start_time) * 1000)
                    SecurityLogger.log_authentication_event(
                        db=db,
                        event_type=event_type,
                        request=request,
                        success=True,
                        description=f"Successful {func.__name__}",
                        response_time_ms=response_time,
                    )

                return result
            except Exception as e:
                # Log failed authentication event
                if request and db:
                    response_time = int((time.time() - start_time) * 1000)
                    SecurityLogger.log_authentication_event(
                        db=db,
                        event_type=event_type,
                        request=request,
                        success=False,
                        description=f"Failed {func.__name__}: {str(e)[:200]}",
                        details={"function": func.__name__, "error": str(e)},
                        response_time_ms=response_time,
                    )
                raise
        return wrapper
    return decorator
