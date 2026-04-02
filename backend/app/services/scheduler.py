"""
Background scheduler for Stock Sentinel.

Handles periodic tasks like alert checking using APScheduler.
"""

import logging
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.services.alert_service import check_all_alerts

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: Optional[BackgroundScheduler] = None


def get_scheduler() -> Optional[BackgroundScheduler]:
    """Get the global scheduler instance."""
    return _scheduler


def start_scheduler() -> None:
    """
    Start the background scheduler for periodic alert checking.
    
    Starts a BackgroundScheduler that runs alert checking every 30 seconds.
    Safe to call multiple times - subsequent calls are idempotent.
    
    Raises:
        RuntimeError: If scheduler fails to start
    """
    global _scheduler
    
    try:
        if _scheduler is not None and _scheduler.running:
            logger.warning("Scheduler already running, skipping restart")
            return
        
        _scheduler = BackgroundScheduler(daemon=True)
        
        # Add job: Check all alerts every 30 seconds
        _scheduler.add_job(
            func=check_all_alerts,
            trigger=IntervalTrigger(seconds=30),
            id="check_alerts_job",
            name="Check all active alerts",
            replace_existing=True,
            max_instances=1,  # Prevent concurrent executions
            misfire_grace_time=10,  # Allow 10s grace period for missed triggers
        )
        
        _scheduler.start()
        logger.info("✅ Background scheduler started (alert checks every 30 seconds)")
        
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {type(e).__name__}: {e}", exc_info=True)
        raise RuntimeError(f"Scheduler failed to start: {e}") from e


def stop_scheduler() -> None:
    """
    Stop the background scheduler gracefully.
    
    Safe to call multiple times - stopping an already-stopped scheduler is idempotent.
    """
    global _scheduler
    
    try:
        if _scheduler is not None and _scheduler.running:
            _scheduler.shutdown(wait=False)
            logger.info("✅ Background scheduler stopped")
        else:
            logger.debug("Scheduler not running, nothing to stop")
    except Exception as e:
        logger.error(f"❌ Error stopping scheduler: {type(e).__name__}: {e}", exc_info=True)


# ============================================================================
# Scheduler management utilities
# ============================================================================

def pause_scheduler() -> None:
    """Pause the scheduler (temporarily stops job execution)."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.pause()
        logger.info("⏸️  Scheduler paused")


def resume_scheduler() -> None:
    """Resume the scheduler (resumes job execution)."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.resume()
        logger.info("▶️  Scheduler resumed")


def is_scheduler_running() -> bool:
    """Check if scheduler is currently running."""
    return _scheduler is not None and _scheduler.running
