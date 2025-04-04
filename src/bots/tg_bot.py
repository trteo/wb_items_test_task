import re

from aiogram import Dispatcher, Bot, Router, F
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger

from settings.config import settings
from src.scrappers.wildberries import WildberriesProductScrapper

WILDBERRIES_PRODUCT_URL_PATTERN = r'wildberries\.ru/catalog/\d+/detail\.aspx'


class TelegramBot:
    def __init__(self) -> None:
        self._bot = Bot(token=settings.BOT_TOKEN.get_secret_value())
        self._router = Router()

        self._dp = Dispatcher()
        self._dp.include_router(self._router)

        self._wb_crapper = WildberriesProductScrapper()

    async def start_bot(self) -> None:
        logger.info('Запуск ТГ бота')

        await self._wb_crapper.init()

        self.__register_routs()
        await self._dp.start_polling(self._bot)

    async def stop_bot(self) -> None:
        logger.info('Остановка ТГ бота')

        await self._wb_crapper.close()
        await self._bot.session.close()

        logger.info('Бот завершен успешно')

    def __register_routs(self) -> None:
        @self._router.message(Command('help'))
        async def start(message: Message):
            """ Возвращает информацию как пользоваться ботом """

            logger.info(f'В боте был нажат help пользователем {message.from_user}')
            await message.reply(
                "Отправь ссылку на товар и я верну тебе позиции товара по 6 запросам, основанных на описании товара"
            )

        @self._router.message(F.text.regexp(fr'.*{WILDBERRIES_PRODUCT_URL_PATTERN}.*'))
        async def wildberries_product_processing(message: Message):
            """
            Обрабатывает сообщение, если в нем присутствует подобная подстрока:
                `wildberries.ru/catalog/12456789/detail.aspx`
            Возвращает позиции товара на странице в зависимости от запроса.
            Запросы формируются из описания товара.

            * Вырезает ссылку из полученного сообщения
            * Пытается получить описание товара
            * Выделяет потенциальные запросы
            * Запускает поиск позиций товара на сайте

            * Отвечает на сообщение списком из: `Запрос`, `№ страницы`, `№ позиции на`, `Ссылка на страницу`
            """

            try:
                cropped_url = 'https://www.' + re.search(
                    rf'({WILDBERRIES_PRODUCT_URL_PATTERN})', message.text
                ).group()
                logger.debug(f'Выделен адрес на товар: {cropped_url}')

                # product description block
                product_scrapper = await self._wb_crapper.get_product_description(url=cropped_url)
                logger.debug(f'Описание товара: {product_scrapper}\n Если оно верное, то первый бастион взят!!!')

                # query extracting block

                # search positions block

                await message.reply(cropped_url)
            except Exception as e:
                await message.reply(f'При запросе произошла ошибка:\n{e}')

