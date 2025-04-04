import asyncio

from src.bots.tg_bot import TelegramBot

if __name__ == "__main__":
    asyncio.run(TelegramBot().start_bot())
