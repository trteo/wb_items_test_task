import re
import sys
from typing import Dict

from aiogram import Dispatcher, Bot, Router, F
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger

from settings.config import settings
from src.queries_extraction.rake import RAKEQueryExtractor
from src.scrappers.models import ProductPosition
from src.scrappers.wildberries.wildberries_product import WildberriesProductScrapper
from src.scrappers.wildberries.wildberries_catalog import WildberriesCatalogScrapper

logger.remove()
logger.add(sys.stderr, level="INFO")


WILDBERRIES_PRODUCT_URL_PATTERN = r'wildberries\.ru/catalog/\d+/detail\.aspx'


class TelegramBot:
    """
    Класс отвечает за принятие и обработку сообщений из ТГ бота.
    Требует для работы определения переменой BOT_TOKEN в переменных окружения settings.env
    """

    def __init__(self) -> None:
        self._bot = Bot(token=settings.BOT_TOKEN.get_secret_value())
        self._router = Router()

        self._dp = Dispatcher()
        self._dp.include_router(self._router)

        self._wb_product_scrapper = WildberriesProductScrapper()
        self._wb_catalog_scrapper = WildberriesCatalogScrapper()

        self._queries_extractor = RAKEQueryExtractor()

    async def start_bot(self) -> None:
        logger.info('Запуск ТГ бота')

        await self._wb_product_scrapper.init()
        await self._wb_catalog_scrapper.init()

        self.__register_routs()
        await self._dp.start_polling(self._bot)

    async def stop_bot(self) -> None:
        logger.info('Остановка ТГ бота')

        await self._wb_product_scrapper.close()
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
                logger.debug(f'Выделен адрес на <a href="{cropped_url}">товар</a>', parse_mode="HTML")

                replied_message = await message.reply(f'Начинаю поиск потенциальных запросов для товара: {cropped_url}')

                # query extracting block

                queries = self._queries_extractor.extract_query_from_description(product_scrapper)
                logger.debug(f'Возможные запросы товара: {queries}\n Если оно хоть немного похоже на правду (нет), то мы прошли ВТОРОЙ бастион!!!')

                # search positions block

                positions = await self._wb_crapper.find_product_positions(product_url=cropped_url, queries=queries)
                logger.info(f'По выделенным запросам товар находится на: {positions}')

                # forming answer

                reply = self.__format_response_message(queries_positions=positions)

                logger.info(f'Попытка отправить сообщение:\n {reply}')
                await replied_message.edit_text(reply, parse_mode="HTML")

            except Exception as e:
                await message.reply(f'При запросе произошла ошибка:\n{e}')
                raise e

    @staticmethod
    def __format_response_message(queries_positions: Dict[str, ProductPosition]) -> str:
        """ Формируем ответ содержащий позиции товаров в зависимости от запросов """
        message_lines = ["Товар по запросам:\n"]

        for query, position in queries_positions.items():
            position_text = (
                f'найден на {position.page_number} странице {position.position_on_page} позиции\n'
                f'<a href="{position.page_url}">ссылка на страницу</a>'
                if position else 'не найден\n'
            )
            message_lines.append(f'<b>{query}</b>: {position_text}')

        return '\n'.join(message_lines)


