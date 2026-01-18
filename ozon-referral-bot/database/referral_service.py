from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from .models import Referral, ReferralCreate
from .database import SessionLocal
import logging

logger = logging.getLogger(__name__)

class ReferralService:
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()

    def create_referral(self, telegram_user_id: int, referral_data: ReferralCreate) -> Referral:
        """Создать новую запись реферала"""
        db_referral = Referral(
            telegram_user_id=telegram_user_id,
            referrer_first_name=referral_data.referrer_first_name,
            referrer_phone=referral_data.referrer_phone,
            referrer_email=referral_data.referrer_email,
            candidate_full_name=referral_data.candidate_full_name,
            candidate_phone=referral_data.candidate_phone,
            vacancy_type=referral_data.vacancy_type,
            citizenship_id=referral_data.citizenship_id,
            city_id=referral_data.city_id,
            hire_object_uuid=referral_data.hire_object_uuid
        )

        self.db.add(db_referral)
        self.db.commit()
        self.db.refresh(db_referral)

        logger.info(f"Created new referral ID {db_referral.id} for user {telegram_user_id}")
        return db_referral

    def get_pending_submissions(self, limit: int = 50) -> List[Referral]:
        """Получить рефералов, ожидающих отправки на Ozon"""
        return self.db.query(Referral).filter(
            and_(
                Referral.submitted_to_ozon == False,
                Referral.submission_attempts < 3
            )
        ).order_by(Referral.created_at).limit(limit).all()

    def update_submission_status(self, referral_id: int, success: bool, error: str = None):
        """Обновить статус отправки реферала"""
        referral = self.db.query(Referral).filter(Referral.id == referral_id).first()
        if not referral:
            logger.error(f"Referral ID {referral_id} not found")
            return

        referral.submission_attempts += 1
        referral.last_submission_attempt = datetime.utcnow()

        if success:
            referral.submitted_to_ozon = True
            referral.submission_error = None
            logger.info(f"Referral ID {referral_id} successfully submitted")
        else:
            referral.submission_error = error
            logger.warning(f"Referral ID {referral_id} submission failed: {error}")

        self.db.commit()

    def get_referral_by_id(self, referral_id: int) -> Optional[Referral]:
        """Получить реферала по ID"""
        return self.db.query(Referral).filter(Referral.id == referral_id).first()

    def get_user_referrals(self, telegram_user_id: int) -> List[Referral]:
        """Получить все рефералы пользователя"""
        return self.db.query(Referral).filter(
            Referral.telegram_user_id == telegram_user_id
        ).order_by(Referral.created_at.desc()).all()

    def get_failed_submissions(self, hours_ago: int = 24) -> List[Referral]:
        """Получить рефералов с неудачными отправками за последние N часов"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_ago)
        return self.db.query(Referral).filter(
            and_(
                Referral.submitted_to_ozon == False,
                Referral.last_submission_attempt >= cutoff_time,
                Referral.submission_attempts >= 3
            )
        ).all()

    def get_submission_stats(self) -> Dict[str, int]:
        """Получить статистику отправок"""
        total = self.db.query(Referral).count()
        submitted = self.db.query(Referral).filter(Referral.submitted_to_ozon == True).count()
        pending = self.db.query(Referral).filter(
            and_(
                Referral.submitted_to_ozon == False,
                Referral.submission_attempts < 3
            )
        ).count()
        failed = self.db.query(Referral).filter(
            and_(
                Referral.submitted_to_ozon == False,
                Referral.submission_attempts >= 3
            )
        ).count()

        return {
            "total": total,
            "submitted": submitted,
            "pending": pending,
            "failed": failed
        }