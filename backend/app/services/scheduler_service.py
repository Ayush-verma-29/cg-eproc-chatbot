# backend/app/services/scheduler_service.py
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.gem_scraper_service import gem_scraper_service

logger = logging.getLogger("scheduler_service")
logger.setLevel(logging.INFO)

scheduler = AsyncIOScheduler()

async def run_nightly_gem_scraper_task():
    """Background task running at 2:00 AM off-peak to refresh GeM catalog items."""
    logger.info("[APScheduler] Starting Nightly GeM Catalog Auto-Refresh (2:00 AM)...")
    try:
        results = await gem_scraper_service.scrape_all_categories()
        logger.info(f"[APScheduler] Nightly GeM Refresh Completed for {len(results)} category streams.")
    except Exception as e:
        logger.error(f"[APScheduler] Nightly GeM Refresh Error: {e}")

def start_scheduler():
    """Initializes and starts the embedded APScheduler inside FastAPI process."""
    if not scheduler.running:
        # Schedule cron trigger for 2:00 AM daily
        trigger = CronTrigger(hour=2, minute=0)
        scheduler.add_job(
            run_nightly_gem_scraper_task,
            trigger=trigger,
            id="nightly_gem_scraper",
            replace_existing=True
        )
        scheduler.start()
        logger.info("[APScheduler] GeM Catalog Background Scheduler started (Trigger: Daily 2:00 AM).")

def stop_scheduler():
    """Shuts down APScheduler gracefully on FastAPI shutdown."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[APScheduler] GeM Catalog Background Scheduler shut down.")
