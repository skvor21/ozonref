from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from database.referral_service import ReferralService
from api.ozon_client import OzonAPIClient
from config.settings import SUBMIT_INTERVAL_MINUTES
import logging
import asyncio

logger = logging.getLogger(__name__)

class SubmissionScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.referral_service = ReferralService()
        self.ozon_client = OzonAPIClient()

    async def submit_pending_referrals(self):
        """Отправить ожидающие рефералы на Ozon"""
        try:
            logger.info("Starting scheduled submission of pending referrals")

            pending_referrals = self.referral_service.get_pending_submissions(limit=10)

            if not pending_referrals:
                logger.info("No pending referrals to submit")
                return

            logger.info(f"Found {len(pending_referrals)} pending referrals to submit")

            for referral in pending_referrals:
                try:
                    result = self.ozon_client.submit_referral(referral)

                    success = result["success"]
                    error = result.get("error")

                    self.referral_service.update_submission_status(
                        referral.id,
                        success=success,
                        error=error
                    )

                    # Небольшая пауза между запросами
                    await asyncio.sleep(1)

                except Exception as e:
                    logger.error(f"Error submitting referral ID {referral.id}: {str(e)}")
                    self.referral_service.update_submission_status(
                        referral.id,
                        success=False,
                        error=str(e)
                    )

        except Exception as e:
            logger.error(f"Error in scheduled submission: {str(e)}")

    def start(self):
        """Запустить планировщик"""
        # Добавляем задачу на отправку каждые N минут
        self.scheduler.add_job(
            self.submit_pending_referrals,
            trigger=IntervalTrigger(minutes=SUBMIT_INTERVAL_MINUTES),
            id="submit_referrals",
            name="Submit pending referrals to Ozon"
        )

        logger.info(f"Starting scheduler with {SUBMIT_INTERVAL_MINUTES} minute intervals")
        self.scheduler.start()

    def stop(self):
        """Остановить планировщик"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")

    async def submit_immediately(self, referral_id: int = None):
        """Отправить реферал немедленно (по запросу)"""
        if referral_id:
            # Отправить конкретный реферал
            referral = self.referral_service.get_referral_by_id(referral_id)
            if not referral:
                logger.error(f"Referral ID {referral_id} not found")
                return False

            result = self.ozon_client.submit_referral(referral)
            self.referral_service.update_submission_status(
                referral.id,
                success=result["success"],
                error=result.get("error")
            )
            return result["success"]
        else:
            # Отправить все ожидающие
            await self.submit_pending_referrals()
            return True