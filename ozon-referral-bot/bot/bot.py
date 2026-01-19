import logging
import asyncio
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
from config.settings import TELEGRAM_BOT_TOKEN, CITIES, CITIZENSHIPS, DEFAULT_VACANCY_DATA
from database.referral_service import ReferralService
from database.models import ReferralCreate
from .scheduler import SubmissionScheduler
import re

# Состояния диалога
REFERRER_NAME, REFERRER_PHONE, REFERRER_EMAIL, CANDIDATE_NAME, CANDIDATE_PHONE, CITY, CITIZENSHIP, CONFIRMATION = range(8)

logger = logging.getLogger(__name__)

class OzonReferralBot:
    def __init__(self):
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self.referral_service = ReferralService()
        self.scheduler = SubmissionScheduler()

        # Настраиваем обработчики
        self.setup_handlers()

    def setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""

        # Conversation handler для сбора данных реферала
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start_referral)],
            states={
                REFERRER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.referrer_name)],
                REFERRER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.referrer_phone)],
                REFERRER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.referrer_email)],
                CANDIDATE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.candidate_name)],
                CANDIDATE_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.candidate_phone)],
                CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.select_city)],
                CITIZENSHIP: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.select_citizenship)],
                CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.confirmation)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

        # Добавляем обработчики
        self.application.add_handler(conv_handler)
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("submit_now", self.submit_now_command))

    async def start_referral(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Начало диалога сбора данных реферала"""
        user = update.effective_user

        # Инициализируем данные пользователя в context
        context.user_data.clear()
        context.user_data['telegram_user_id'] = user.id

        await update.message.reply_text(
            f"Привет, {user.first_name}! 👋\n\n"
            "Я помогу вам отправить реферала на вакансию курьера-кладовщика в Ozon.\n\n"
            "Пожалуйста, введите ваше ФИО (реферала):"
        )

        return REFERRER_NAME

    async def referrer_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Сбор ФИО реферала"""
        name = update.message.text.strip()

        if len(name) < 2:
            await update.message.reply_text("Пожалуйста, введите корректное ФИО (минимум 2 символа):")
            return REFERRER_NAME

        context.user_data['referrer_first_name'] = name

        await update.message.reply_text(
            "Отлично! Теперь введите ваш номер телефона в формате +7(XXX)XXX-XX-XX:"
        )

        return REFERRER_PHONE

    async def referrer_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Сбор телефона реферала"""
        phone = update.message.text.strip()

        # Проверяем формат телефона
        phone_pattern = r'^\+7\(\d{3}\)\d{3}-\d{2}-\d{2}$'
        if not re.match(phone_pattern, phone):
            await update.message.reply_text(
                "Неверный формат телефона. Используйте формат +7(XXX)XXX-XX-XX:"
            )
            return REFERRER_PHONE

        context.user_data['referrer_phone'] = phone

        await update.message.reply_text("Введите ваш email адрес:")

        return REFERRER_EMAIL

    async def referrer_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Сбор email реферала"""
        email = update.message.text.strip().lower()

        # Простая проверка email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            await update.message.reply_text("Неверный формат email. Попробуйте еще раз:")
            return REFERRER_EMAIL

        context.user_data['referrer_email'] = email

        await update.message.reply_text(
            "Теперь введите ФИО кандидата (того, кого вы рекомендуете):"
        )

        return CANDIDATE_NAME

    async def candidate_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Сбор ФИО кандидата"""
        name = update.message.text.strip()

        if len(name) < 2:
            await update.message.reply_text("Пожалуйста, введите корректное ФИО кандидата:")
            return CANDIDATE_NAME

        context.user_data['candidate_full_name'] = name

        await update.message.reply_text(
            "Введите номер телефона кандидата в формате +7(XXX)XXX-XX-XX:"
        )

        return CANDIDATE_PHONE

    async def candidate_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Сбор телефона кандидата"""
        phone = update.message.text.strip()

        phone_pattern = r'^\+7\(\d{3}\)\d{3}-\d{2}-\d{2}$'
        if not re.match(phone_pattern, phone):
            await update.message.reply_text(
                "Неверный формат телефона. Используйте формат +7(XXX)XXX-XX-XX:"
            )
            return CANDIDATE_PHONE

        context.user_data['candidate_phone'] = phone

        # Показываем список доступных городов
        city_keyboard = [[city] for city in CITIES.keys()]
        city_keyboard.append(["Отмена"])

        await update.message.reply_text(
            "Выберите город для работы:",
            reply_markup=ReplyKeyboardMarkup(city_keyboard, one_time_keyboard=True)
        )

        return CITY

    async def select_city(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Выбор города"""
        city_name = update.message.text.strip()

        if city_name == "Отмена":
            await update.message.reply_text("Операция отменена.", reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END

        if city_name not in CITIES:
            await update.message.reply_text(
                "Пожалуйста, выберите город из списка или введите 'Отмена':"
            )
            return CITY

        context.user_data['city_name'] = city_name
        context.user_data['city_id'] = CITIES[city_name]

        # Показываем список гражданств
        citizenship_keyboard = [[country] for country in CITIZENSHIPS.keys()]
        citizenship_keyboard.append(["Отмена"])

        await update.message.reply_text(
            "Выберите гражданство кандидата:",
            reply_markup=ReplyKeyboardMarkup(citizenship_keyboard, one_time_keyboard=True)
        )

        return CITIZENSHIP

    async def select_citizenship(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Выбор гражданства"""
        citizenship_name = update.message.text.strip()

        if citizenship_name == "Отмена":
            await update.message.reply_text("Операция отменена.", reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END

        if citizenship_name not in CITIZENSHIPS:
            await update.message.reply_text(
                "Пожалуйста, выберите гражданство из списка или введите 'Отмена':"
            )
            return CITIZENSHIP

        context.user_data['citizenship_name'] = citizenship_name
        context.user_data['citizenship_id'] = CITIZENSHIPS[citizenship_name]

        # Показываем сводку для подтверждения
        vacancy_data = DEFAULT_VACANCY_DATA["courier_sklad"]

        summary = (
            "📋 Проверьте данные:\n\n"
            f"👤 Реферал: {context.user_data['referrer_first_name']}\n"
            f"📞 Телефон реферала: {context.user_data['referrer_phone']}\n"
            f"📧 Email реферала: {context.user_data['referrer_email']}\n\n"
            f"👥 Кандидат: {context.user_data['candidate_full_name']}\n"
            f"📞 Телефон кандидата: {context.user_data['candidate_phone']}\n"
            f"🏙️ Город: {context.user_data['city_name']}\n"
            f"🇷🇺 Гражданство: {context.user_data['citizenship_name']}\n\n"
            f"💼 Вакансия: Курьер-кладовщик\n\n"
            "✅ Все верно? Отправьте 'Да' для подтверждения или 'Нет' для отмены:"
        )

        await update.message.reply_text(summary, reply_markup=ReplyKeyboardRemove())

        return CONFIRMATION

    async def confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Подтверждение и сохранение данных"""
        response = update.message.text.strip().lower()

        if response not in ['да', 'yes', 'y']:
            await update.message.reply_text(
                "Операция отменена. Вы можете начать заново командой /start"
            )
            return ConversationHandler.END

        try:
            # Создаем объект с данными реферала
            vacancy_data = DEFAULT_VACANCY_DATA["courier_sklad"]

            referral_data = ReferralCreate(
                referrer_first_name=context.user_data['referrer_first_name'],
                referrer_phone=context.user_data['referrer_phone'],
                referrer_email=context.user_data['referrer_email'],
                candidate_full_name=context.user_data['candidate_full_name'],
                candidate_phone=context.user_data['candidate_phone'],
                vacancy_type=vacancy_data["combineCustomerVacancy"],
                citizenship_id=context.user_data['citizenship_id'],
                city_id=context.user_data['city_id'],
                hire_object_uuid=vacancy_data["hireObjectUUID"]
            )

            # Сохраняем в базу данных
            referral = self.referral_service.create_referral(
                context.user_data['telegram_user_id'],
                referral_data
            )

            # Попытка немедленной отправки
            await self.scheduler.submit_immediately(referral.id)

            await update.message.reply_text(
                "✅ Спасибо! Данные успешно сохранены и отправлены на обработку в Ozon.\n\n"
                f"ID вашей заявки: {referral.id}\n\n"
                "Вы можете отправить еще одного кандидата командой /start\n"
                "или посмотреть статистику командой /stats"
            )

        except Exception as e:
            logger.error(f"Error saving referral: {str(e)}")
            await update.message.reply_text(
                "❌ Произошла ошибка при сохранении данных. Попробуйте еще раз командой /start"
            )

        return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Отмена диалога"""
        await update.message.reply_text(
            "Операция отменена. Вы можете начать заново командой /start",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать справку"""
        help_text = (
            "🤖 Бот для рефералов Ozon\n\n"
            "📝 /start - Начать процесс реферала\n"
            "📊 /stats - Посмотреть статистику\n"
            "🚀 /submit_now - Принудительно отправить ожидающие заявки\n"
            "❓ /help - Показать эту справку\n\n"
            "Бот автоматически отправляет данные на серверы Ozon каждые 5 минут."
        )
        await update.message.reply_text(help_text)

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать статистику"""
        try:
            stats = self.referral_service.get_submission_stats()

            stats_text = (
                "📊 Статистика рефералов:\n\n"
                f"📄 Всего заявок: {stats['total']}\n"
                f"✅ Отправлено в Ozon: {stats['submitted']}\n"
                f"⏳ Ожидает отправки: {stats['pending']}\n"
                f"❌ Ошибки отправки: {stats['failed']}\n"
            )

            await update.message.reply_text(stats_text)

        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            await update.message.reply_text("❌ Ошибка при получении статистики")

    async def submit_now_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Принудительная отправка ожидающих заявок"""
        try:
            await update.message.reply_text("🚀 Запускаю отправку ожидающих заявок...")

            await self.scheduler.submit_immediately()

            await update.message.reply_text("✅ Отправка завершена!")

        except Exception as e:
            logger.error(f"Error in manual submission: {str(e)}")
            await update.message.reply_text("❌ Ошибка при отправке заявок")

    def run(self):
        """Запуск бота"""
        logger.info("Starting Ozon Referral Bot...")

        # Запускаем планировщик в фоне
        self.scheduler.start()

        # Запускаем бота
        self.application.run_polling()