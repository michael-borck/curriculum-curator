"""
Monitoring and health check endpoints
"""

import os
from datetime import datetime, timedelta
from typing import Any

import psutil
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.models import LoginAttempt, SecurityLog, User, UserRole

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "curriculum-curator-backend",
        "version": settings.VERSION if hasattr(settings, "VERSION") else "1.0.0",
    }


@router.get("/health/detailed")
async def detailed_health_check(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_user),
):
    """
    Detailed health check with system metrics (admin only)
    """
    health_status: dict[str, Any] = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {},
        "metrics": {},
    }

    # Database check
    try:
        result = db.execute(text("SELECT 1"))
        db_status = "healthy" if result.scalar() == 1 else "unhealthy"
    except Exception as e:
        db_status = f"unhealthy: {e!s}"
    health_status["checks"]["database"] = db_status

    # System metrics
    try:
        health_status["metrics"]["cpu"] = {
            "percent": psutil.cpu_percent(interval=1),
            "count": psutil.cpu_count(),
        }

        memory = psutil.virtual_memory()
        health_status["metrics"]["memory"] = {
            "percent": memory.percent,
            "used_gb": round(memory.used / (1024**3), 2),
            "total_gb": round(memory.total / (1024**3), 2),
        }

        disk = psutil.disk_usage("/")
        health_status["metrics"]["disk"] = {
            "percent": disk.percent,
            "used_gb": round(disk.used / (1024**3), 2),
            "total_gb": round(disk.total / (1024**3), 2),
        }
    except Exception as e:
        health_status["metrics"]["error"] = str(e)

    # Application metrics
    try:
        # User statistics
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        verified_users = db.query(User).filter(User.is_verified == True).count()

        health_status["metrics"]["users"] = {
            "total": total_users,
            "active": active_users,
            "verified": verified_users,
        }

        # Recent login attempts (last hour)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_attempts = (
            db.query(LoginAttempt)
            .filter(LoginAttempt.attempted_at > one_hour_ago)
            .count()
        )
        failed_attempts = (
            db.query(LoginAttempt)
            .filter(LoginAttempt.attempted_at > one_hour_ago)
            .filter(LoginAttempt.success == False)
            .count()
        )

        health_status["metrics"]["authentication"] = {
            "recent_attempts": recent_attempts,
            "recent_failures": failed_attempts,
        }
    except Exception as e:
        health_status["metrics"]["app_error"] = str(e)

    # Overall status determination
    if db_status != "healthy":
        health_status["status"] = "degraded"

    return health_status


@router.get("/metrics")
async def get_metrics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_user),
):
    """
    Get application metrics for monitoring (admin only)
    """
    now = datetime.utcnow()

    metrics: dict[str, Any] = {
        "timestamp": now.isoformat(),
        "period": "last_24_hours",
        "authentication": {},
        "security": {},
        "content": {},
        "system": {},
    }

    # Authentication metrics (last 24 hours)
    one_day_ago = now - timedelta(days=1)

    # Login attempts
    login_attempts = db.query(LoginAttempt).filter(
        LoginAttempt.attempted_at > one_day_ago
    )
    successful_logins = login_attempts.filter(LoginAttempt.success == True).count()
    failed_logins = login_attempts.filter(LoginAttempt.success == False).count()

    metrics["authentication"] = {
        "successful_logins": successful_logins,
        "failed_logins": failed_logins,
        "failure_rate": round(
            failed_logins / max(successful_logins + failed_logins, 1) * 100, 2
        ),
        "unique_ips": login_attempts.distinct(LoginAttempt.ip_address).count(),
    }

    # Security events
    security_events = db.query(SecurityLog).filter(SecurityLog.timestamp > one_day_ago)

    metrics["security"] = {
        "total_events": security_events.count(),
        "high_severity": security_events.filter(SecurityLog.severity == "HIGH").count(),
        "medium_severity": security_events.filter(
            SecurityLog.severity == "MEDIUM"
        ).count(),
        "low_severity": security_events.filter(SecurityLog.severity == "LOW").count(),
    }

    # User metrics
    new_users = db.query(User).filter(User.created_at > one_day_ago).count()

    metrics["users"] = {
        "new_registrations": new_users,
        "total_users": db.query(User).count(),
        "admin_users": db.query(User).filter(User.role == UserRole.ADMIN.value).count(),
    }

    # System metrics
    metrics["system"] = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "python_version": os.sys.version.split()[0],
    }

    return metrics


@router.get("/alerts")
async def get_alerts(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_user),
):
    """
    Get active security alerts (admin only)
    """
    alerts = []
    now = datetime.utcnow()

    # Check for high failed login rate
    one_hour_ago = now - timedelta(hours=1)
    recent_failures = (
        db.query(LoginAttempt)
        .filter(LoginAttempt.attempted_at > one_hour_ago)
        .filter(LoginAttempt.success == False)
        .count()
    )

    if recent_failures > 50:  # Threshold
        alerts.append(
            {
                "level": "WARNING",
                "type": "authentication",
                "message": f"High number of failed login attempts: {recent_failures} in the last hour",
                "timestamp": now.isoformat(),
            }
        )

    # Check for locked accounts
    from sqlalchemy import and_

    locked_accounts = (
        db.query(LoginAttempt)
        .filter(
            and_(
                LoginAttempt.locked_until != None,  # noqa: E711
                LoginAttempt.locked_until > now,  # type: ignore[operator]
            )
        )
        .distinct(LoginAttempt.email)
        .count()
    )

    if locked_accounts > 0:
        alerts.append(
            {
                "level": "INFO",
                "type": "authentication",
                "message": f"{locked_accounts} account(s) currently locked",
                "timestamp": now.isoformat(),
            }
        )

    # Check system resources
    cpu_percent = psutil.cpu_percent(interval=1)
    if cpu_percent > 80:
        alerts.append(
            {
                "level": "WARNING",
                "type": "system",
                "message": f"High CPU usage: {cpu_percent}%",
                "timestamp": now.isoformat(),
            }
        )

    memory_percent = psutil.virtual_memory().percent
    if memory_percent > 85:
        alerts.append(
            {
                "level": "WARNING",
                "type": "system",
                "message": f"High memory usage: {memory_percent}%",
                "timestamp": now.isoformat(),
            }
        )

    disk_percent = psutil.disk_usage("/").percent
    if disk_percent > 90:
        alerts.append(
            {
                "level": "CRITICAL",
                "type": "system",
                "message": f"Critical disk usage: {disk_percent}%",
                "timestamp": now.isoformat(),
            }
        )

    # Check for suspicious activity patterns
    fifteen_min_ago = now - timedelta(minutes=15)
    rapid_attempts = (
        db.query(LoginAttempt)
        .filter(LoginAttempt.attempted_at > fifteen_min_ago)
        .filter(LoginAttempt.success == False)
        .group_by(LoginAttempt.ip_address)
        .having(text("COUNT(*) > 10"))
        .count()
    )

    if rapid_attempts > 0:
        alerts.append(
            {
                "level": "WARNING",
                "type": "security",
                "message": f"Potential brute force attempts from {rapid_attempts} IP(s)",
                "timestamp": now.isoformat(),
            }
        )

    return {
        "alerts": alerts,
        "total": len(alerts),
        "timestamp": now.isoformat(),
    }


@router.post("/test-alert")
async def test_alert(
    alert_type: str = "test",
    current_user: User = Depends(deps.get_current_admin_user),
):
    """
    Generate a test alert for monitoring system validation (admin only)
    """
    return {
        "status": "success",
        "message": f"Test alert of type '{alert_type}' generated",
        "timestamp": datetime.utcnow().isoformat(),
        "alert": {
            "level": "INFO",
            "type": alert_type,
            "message": "This is a test alert for monitoring system validation",
        },
    }
