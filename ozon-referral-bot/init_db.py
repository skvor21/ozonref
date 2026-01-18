#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных
"""

import logging
from database.database import init_db
from loguru import logger

def main():
    """Инициализация базы данных"""
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully!")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()