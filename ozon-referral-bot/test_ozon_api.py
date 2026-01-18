#!/usr/bin/env python3
"""
Скрипт для тестирования API Ozon
"""

import json
from api.ozon_client import OzonAPIClient
from database.models import Referral
from loguru import logger

def create_test_referral():
    """Создать тестовый реферал"""
    return Referral(
        id=1,
        telegram_user_id=123456789,
        referrer_first_name="Тестовый Реферал",
        referrer_phone="+7(999)123-45-67",
        referrer_email="test@example.com",
        candidate_full_name="Тестовый Кандидат",
        candidate_phone="+7(999)987-65-43",
        vacancy_type="ff:truckDriver",
        citizenship_id=7,
        city_id="73d7119e-1e3c-11e9-90e9-9418826ee072",
        hire_object_uuid="51761b1a-1c00-11ef-9463-525400d5f71a",
        submitted_to_ozon=False,
        submission_attempts=0
    )

def test_ozon_connection():
    """Тест подключения к Ozon"""
    client = OzonAPIClient()

    logger.info("Testing Ozon API connection...")
    connection_ok = client.test_connection()

    if connection_ok:
        logger.info("✅ Connection to Ozon OK")
    else:
        logger.error("❌ Connection to Ozon FAILED")
        return False

    return True

def test_referral_submission():
    """Тест отправки реферала"""
    client = OzonAPIClient()
    test_referral = create_test_referral()

    logger.info("Testing referral submission...")
    result = client.submit_referral(test_referral)

    if result["success"]:
        logger.info("✅ Referral submission OK")
        logger.info(f"Response: {result['response_text']}")
    else:
        logger.error("❌ Referral submission FAILED")
        logger.error(f"Error: {result['error']}")

    return result["success"]

def main():
    """Главная функция тестирования"""
    logger.info("Starting Ozon API tests...")

    # Тест подключения
    if not test_ozon_connection():
        logger.error("Connection test failed, aborting...")
        return

    # Тест отправки (только если указано)
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--submit":
        logger.warning("⚠️  This will send a REAL request to Ozon API!")
        confirm = input("Are you sure? (yes/no): ")
        if confirm.lower() == "yes":
            test_referral_submission()
        else:
            logger.info("Submission test skipped")
    else:
        logger.info("Run with --submit to test actual submission")

    logger.info("Tests completed!")

if __name__ == "__main__":
    main()