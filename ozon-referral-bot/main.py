#!/usr/bin/env python3
"""
Ozon Referral Bot - Telegram бот для сбора рефералов и автоматической отправки на Ozon

Запуск:
    python main.py

Требуемые переменные окружения:
    TELEGRAM_BOT_TOKEN - токен Telegram бота
    DATABASE_URL - URL подключения к PostgreSQL (опционально, по умолчанию sqlite)
    REDIS_URL - URL Redis (опционально)
    OZON_COOKIE - Cookie для Ozon API (опционально)
"""

import logging
import sys
from loguru import logger
from config.settings import LOG_LEVEL, LOG_FILE
from database.database import init_db
from bot.bot import OzonReferralBot

def setup_logging():
    """Настройка логирования"""
    # Удаляем стандартный обработчик
    logging.getLogger().handlers.clear()

    # Настраиваем loguru
    logger.remove()
    logger.add(
        sys.stdout,
        level=LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )

    # Добавляем файл логов
    logger.add(
        LOG_FILE,
        level=LOG_LEVEL,
        rotation="10 MB",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )

    # Перенаправляем стандартное логирование в loguru
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            logger_opt = logger.opt(depth=6, exception=record.exc_info)
            logger_opt.log(record.levelname, record.getMessage())

    logging.getLogger().addHandler(InterceptHandler())
    logging.getLogger().setLevel(LOG_LEVEL)

def main():
    """Главная функция"""
    try:
        # Настраиваем логирование
        setup_logging()

        logger.info("Starting Ozon Referral Bot...")

        # Инициализируем базу данных
        logger.info("Initializing database...")
        init_db()

        # Создаем и запускаем бота
        logger.info("Starting Telegram bot...")
        bot = OzonReferralBot()
        bot.run()

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()