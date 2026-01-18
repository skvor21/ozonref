from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

Base = declarative_base()

class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True)
    telegram_user_id = Column(Integer, nullable=False)

    # Данные реферала (того, кто приглашает)
    referrer_first_name = Column(String(255), nullable=False)
    referrer_phone = Column(String(50), nullable=False)
    referrer_email = Column(String(255), nullable=False)

    # Данные кандидата (того, кого приглашают)
    candidate_full_name = Column(String(255), nullable=False)
    candidate_phone = Column(String(50), nullable=False)

    # Данные вакансии
    vacancy_type = Column(String(100), nullable=False)  # combineCustomerVacancy
    citizenship_id = Column(Integer, nullable=False)
    city_id = Column(String(100), nullable=False)
    hire_object_uuid = Column(String(100), nullable=False)

    # Системные поля
    utm_source = Column(String(100), default="referral_campaign")
    fullpath = Column(String(500), default="https://recruitment.ozon.ru/ref-courier-sklad")
    rr_flag = Column(String(10), default="1")
    abt_att = Column(String(10), default="1")

    # Статус отправки
    submitted_to_ozon = Column(Boolean, default=False)
    submission_attempts = Column(Integer, default=0)
    last_submission_attempt = Column(DateTime)
    submission_error = Column(Text)

    # Метаданные
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

# Pydantic модели для API
class ReferralCreate(BaseModel):
    referrer_first_name: str
    referrer_phone: str
    referrer_email: str
    candidate_full_name: str
    candidate_phone: str
    vacancy_type: str = "ff:truckDriver"  # По умолчанию курьер-кладовщик
    citizenship_id: int = 7  # По умолчанию Россия
    city_id: str
    hire_object_uuid: str

class ReferralResponse(ReferralCreate):
    id: int
    telegram_user_id: int
    submitted_to_ozon: bool
    submission_attempts: int
    created_at: datetime

    class Config:
        from_attributes = True