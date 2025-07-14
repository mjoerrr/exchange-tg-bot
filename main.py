import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, MODERS_CHAT_ID
from handlers import router


if BOT_TOKEN == '':
    raise Exception('Не указан токен бота, введите его в файле config.py, а затем перезапустите бота')

if MODERS_CHAT_ID == 0:
    raise Exception('Не указан ID чата модераторов, введите его в файле config.py, а затем перезапустите бота')


logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher(storage=storage)

dp.include_router(router)


async def main():
    await bot.delete_webhook(True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())