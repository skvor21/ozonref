import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/ozon_referrals")

# Redis для очередей и кэширования
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Ozon API
OZON_API_URL = "https://sigma-bff-api.ozon.ru/v1/actions"
OZON_HEADERS = {
    "sec-ch-ua-platform": "macOS",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    "Content-Type": "application/json;charset=UTF-8",
    "sec-ch-ua-mobile": "?0",
    "Sec-Fetch-Site": "same-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "origin": "https://recruitment.ozon.ru",
    "referer": "https://recruitment.ozon.ru"
}

# Cookie для Ozon (может меняться, нужно мониторить)
OZON_COOKIE = os.getenv("OZON_COOKIE", "")

# Настройки отправки
SUBMIT_INTERVAL_MINUTES = int(os.getenv("SUBMIT_INTERVAL_MINUTES", "5"))  # Отправка каждые 5 минут
MAX_SUBMISSION_ATTEMPTS = int(os.getenv("MAX_SUBMISSION_ATTEMPTS", "3"))

# Логирование
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/bot.log")

# Данные по умолчанию для вакансий
DEFAULT_VACANCY_DATA = {
    "courier_sklad": {
        "combineCustomerVacancy": "ff:truckDriver",
        "hireObjectUUID": "51761b1a-1c00-11ef-9463-525400d5f71a",
        "fullpath": "https://recruitment.ozon.ru/ref-courier-sklad"
    }
}

# Список городов (можно расширить)
CITIES = {
    "Москва": "73d7119e-1e3c-11e9-90e9-9418826ee072",
    "Санкт-Петербург": "73d7119f-1e3c-11e9-90e9-9418826ee072",
    # Добавить другие города по необходимости
}

# Гражданства
CITIZENSHIPS = {
    "Россия": 7,
    "Казахстан": 8,
    "Беларусь": 9,
    # Добавить другие по необходимости
}