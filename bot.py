import logging
import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramConflictError


import database as db
from handlers import register_handlers
from admin import register_admin_handlers
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Берем токен из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    logger.error("BOT_TOKEN не найден в переменных окружения!")
    exit(1)

"""Основной файл для развертывания проекта"""

# Для Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("=" * 50)
print("🚀 ЗАПУСК БОТА")
print("=" * 50)

# Инициализация БД
db.init_db()

# Создаем бота
bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Регистрируем хендлеры
logger.info("Регистрация админ-обработчиков...")
register_admin_handlers(dp)

logger.info("Регистрация основных обработчиков...")
register_handlers(dp)

logger.info(f"✅ Администраторы: {config.ADMIN_IDS}")

async def main():
    try:
        logger.info("🤖 Бот запущен и готов к работе!")
        logger.info("📋 Доступные команды: /start, /admin")
        await dp.start_polling(bot)
    except TelegramConflictError:
        logger.error("❌ Ошибка: Бот уже запущен в другом месте!")
        logger.info("Закройте все другие экземпляры бота и попробуйте снова.")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
    finally:
        await bot.session.close()
        await storage.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Бот остановлен")
