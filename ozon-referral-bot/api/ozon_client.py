import requests
import json
from typing import Dict, Any, Optional
from config.settings import OZON_API_URL, OZON_HEADERS, OZON_COOKIE
from database.models import Referral
import logging

logger = logging.getLogger(__name__)

class OzonAPIClient:
    def __init__(self):
        self.base_url = OZON_API_URL
        self.headers = OZON_HEADERS.copy()
        if OZON_COOKIE:
            self.headers["Cookie"] = OZON_COOKIE

    def submit_referral(self, referral: Referral) -> Dict[str, Any]:
        """
        Отправить данные реферала на Ozon API

        Args:
            referral: Объект Referral с данными

        Returns:
            Dict с результатом отправки
        """
        payload = {
            "action": "SendReplyRequest",
            "body": json.dumps({
                "referrerFirstName": referral.referrer_first_name,
                "referrerPhone": referral.referrer_phone,
                "referrerEmail": referral.referrer_email,
                "fullName": referral.candidate_full_name,
                "phone": referral.candidate_phone,
                "combineCustomerVacancy": referral.vacancy_type,
                "citizenshipID": referral.citizenship_id,
                "cityID": referral.city_id,
                "hireObjectUUID": referral.hire_object_uuid,
                "utm_source": referral.utm_source,
                "fullpath": referral.fullpath,
                "__rr": referral.rr_flag,
                "abt_att": referral.abt_att
            })
        }

        try:
            logger.info(f"Submitting referral ID {referral.id} to Ozon API")

            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )

            result = {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response_text": response.text,
                "error": None
            }

            if result["success"]:
                logger.info(f"Successfully submitted referral ID {referral.id}")
            else:
                logger.error(f"Failed to submit referral ID {referral.id}: {response.status_code} - {response.text}")
                result["error"] = f"HTTP {response.status_code}: {response.text}"

            return result

        except requests.exceptions.RequestException as e:
            error_msg = f"Request error: {str(e)}"
            logger.error(f"Error submitting referral ID {referral.id}: {error_msg}")
            return {
                "success": False,
                "status_code": None,
                "response_text": None,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Unexpected error submitting referral ID {referral.id}: {error_msg}")
            return {
                "success": False,
                "status_code": None,
                "response_text": None,
                "error": error_msg
            }

    def test_connection(self) -> bool:
        """Тестовое подключение к API"""
        try:
            # Пробуем GET запрос для проверки доступности
            response = requests.get(
                "https://recruitment.ozon.ru",
                headers={"User-Agent": self.headers["User-Agent"]},
                timeout=10
            )
            return response.status_code == 200
        except:
            return False