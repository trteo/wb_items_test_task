import re

from aiogram import Dispatcher, Bot, Router, F
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger

from settings.config import settings

WILDBERRIES_PRODUCT_URL_PATTERN = r'wildberries\.ru/catalog/\d+/detail\.aspx'


class TelegramBot:
    def __init__(self):
        self.bot = Bot(token=settings.BOT_TOKEN.get_secret_value())
        self.router = Router()

        self.dp = Dispatcher()
        self.dp.include_router(self.router)

    async def start_bot(self):
        logger.info('Bot started')

        self.__register_routs()
        await self.dp.start_polling(self.bot)

        logger.info('Bot ended')

    def __register_routs(self):
        @self.router.message(Command('help'))
        async def start(message: Message):
            logger.debug(message.chat)
            logger.debug(message.text)
            logger.debug(message.message_id)
            logger.debug(message.from_user)

            await message.reply("Здесь могла быть ваша реклама")

        @self.router.message(F.text.regexp(fr'.*{WILDBERRIES_PRODUCT_URL_PATTERN}.*'))
        async def wildberries_product_processing(message: Message):
            logger.debug(message.chat)
            logger.debug(f'Получено сообщение: {message.text}\n')
            logger.debug(message.message_id)
            logger.debug(message.from_user)

            cropped_url = re.search(rf'({WILDBERRIES_PRODUCT_URL_PATTERN})', message.text)
            logger.debug(f'Выделен адрес на товар: {cropped_url}')

            # product description block

            # TODO get page by url
            # TODO load details part
            # TODO get description from page

            # query extracting block

            # search positions block

            await message.answer(cropped_url.group())
