"""
Security logger service for tracking security events
"""

import time
from typing import TYPE_CHECKING

from fastapi import Request

from app.models.security_log import SecurityEventType, SecurityLog

if TYPE_CHECKING:
    from app.models import User


class SecurityLogger:
    """Centralized security logging service"""

    @staticmethod
    def log_authentication_event(
        db,
        event_type: SecurityEventType,
        request: Request,
        user: "User | None" = None,
        success: bool = True,
        description: str | None = None,
        details: dict | None = None,
        response_time_ms: int | None = None,
    ):
        """Log authentication-related events"""
        client_ip = SecurityLogger._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "Unknown")

        SecurityLog.log_event(
            db_session=db,
            event_type=event_type,
            ip_address=client_ip,
            user_id=str(user.id) if user else None,
            user_email=user.email if user else None,
            user_role=user.role if user else None,
            user_agent=user_agent,
            request_path=str(request.url.path),
            request_method=request.method,
            event_description=description,
            severity="info" if success else "warning",
            success="success" if success else "failure",
            details=details or {},
            response_time_ms=response_time_ms,
        )

    @staticmethod
    def log_security_event(
        db,
        event_type: SecurityEventType,
        request: Request,
        severity: str = "warning",
        description: str | None = None,
        details: dict | None = None,
        user: "User | None" = None,
        response_time_ms: int | None = None,
    ):
        """Log general security events"""
        client_ip = SecurityLogger._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "Unknown")

        SecurityLog.log_event(
            db_session=db,
            event_type=event_type,
            ip_address=client_ip,
            user_id=str(user.id) if user else None,
            user_email=user.email if user else None,
            user_role=user.role if user else None,
            user_agent=user_agent,
            request_path=str(request.url.path),
            request_method=request.method,
            event_description=description,
            severity=severity,
            success="blocked"
            if severity in ["warning", "error", "critical"]
            else "success",
            details=details or {},
            response_time_ms=response_time_ms,
        )

    @staticmethod
    def log_data_access_event(
        db,
        request: Request,
        user: "User",
        resource_type: str,
        resource_id: str | None = None,
        action: str = "read",
        description: str | None = None,
        response_time_ms: int | None = None,
    ):
        """Log data access events for audit trails"""
        client_ip = SecurityLogger._get_client_ip(request)

        SecurityLog.log_event(
            db_session=db,
            event_type=SecurityEventType.SENSITIVE_DATA_ACCESS,
            ip_address=client_ip,
            user_id=str(user.id),
            user_email=user.email,
            user_role=user.role,
            user_agent=request.headers.get("user-agent", "Unknown"),
            request_path=str(request.url.path),
            request_method=request.method,
            event_description=description or f"Accessed {resource_type}",
            severity="info",
            success="success",
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "action": action,
            },
            response_time_ms=response_time_ms,
        )

    @staticmethod
    def log_admin_action(
        db,
        admin_user,
        action: str,
        target_user_id: str | None = None,
        details: dict | None = None,
    ):
        """Log administrative actions"""
        SecurityLog.log_event(
            db_session=db,
            event_type=SecurityEventType.ADMIN_ACTION,
            ip_address="127.0.0.1",  # Would come from request in real scenario
            user_id=str(admin_user.id),
            user_email=admin_user.email,
            user_role=admin_user.role,
            event_description=action,
            severity="info",
            success="success",
            details={
                "action": action,
                "target_user_id": target_user_id,
                **(details or {}),
            },
        )

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Extract client IP from request, handling proxies"""
        # Check for X-Forwarded-For header (common with proxies/load balancers)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, take the first one
            return forwarded_for.split(",")[0].strip()

        # Check for X-Real-IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return "Unknown"

    @staticmethod
    def analyze_login_patterns(db, user_id: str, hours: int = 24) -> dict:
        """Analyze login patterns for a specific user"""
        events = SecurityLog.get_recent_events(
            db_session=db,
            hours=hours,
            event_types=[
                SecurityEventType.LOGIN_SUCCESS,
                SecurityEventType.LOGIN_FAILED,
            ],
            user_id=user_id,
        )

        success_count = sum(1 for e in events if e.success == "success")
        failure_count = sum(1 for e in events if e.success == "failure")
        unique_ips = len({e.ip_address for e in events})

        # Detect suspicious patterns
        suspicious_patterns = []
        if unique_ips > 5:  # Many different IPs
            suspicious_patterns.append("Multiple IP addresses detected")
        if failure_count > success_count * 2:  # High failure rate
            suspicious_patterns.append("High login failure rate")

        return {
            "total_attempts": len(events),
            "successful_logins": success_count,
            "failed_logins": failure_count,
            "unique_ip_addresses": unique_ips,
            "suspicious_patterns": suspicious_patterns,
        }


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
                elif hasattr(arg, "query"):  # SQLAlchemy session
                    db = arg

            # Look in kwargs as well
            if not request:
                request = kwargs.get("request")
            if not db:
                db = kwargs.get("db")

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
                elif hasattr(arg, "query"):  # SQLAlchemy session
                    db = arg

            # Look in kwargs as well
            if not request:
                request = kwargs.get("request")
            if not db:
                db = kwargs.get("db")

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
