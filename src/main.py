import asyncio

from src.bots.tg_bot import TelegramBot
import nltk

nltk.download('stopwords')
nltk.download('punkt_tab')


if __name__ == '__main__':
    asyncio.run(TelegramBot().start_bot())
