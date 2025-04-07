import asyncio

from loguru import logger

from src.scrappers.exceptions import ProductNotFound
from playwright.async_api import Page
from src.scrappers.wildberries.wildberries_base import WildberriesBaseScrapper


class WildberriesProductScrapper(WildberriesBaseScrapper):
    """
    Класс для скрабинга продуктов Wildberries
        * Поиск описания
    """

    async def get_product_description(self, url: str) -> str:
        """
        Получение описания товара по ссылке

        :param  url: ссылка на товар на Wildberries
        :return: Строка содержащая описание товара
        """
        page = await self._create_page()

        button_description_selector = 'button.j-details-btn-desktop'
        section_description_selector = 'section.product-details__description p.option__text'

        try:
            logger.info(f'Начинаю поиск товара с url: {url}')
            await page.goto(url, wait_until='domcontentloaded')

            logger.info(f'Ожидаем появление кнопки "Характеристики и описание" для товара с url: {url}')
            await page.wait_for_selector(button_description_selector)

            await self.__check_if_product_exist(url=url, page=page)

            logger.info(f'Загружается кнопка получения дополнительной информации для товара с url: {url}!')
            await page.click(button_description_selector)
            await page.wait_for_selector(section_description_selector)

            logger.info(f'Описание товара загрузилось!')
            description_content = await (await page.query_selector(section_description_selector)).text_content()

            logger.info(f'Найдено описание товара для товара с url: {url}:\n {description_content}')
            return description_content
        except ProductNotFound as e:
            logger.error(f'Не удалось найти товар: {url}')
            raise e

    @staticmethod
    async def __check_if_product_exist(url: str, page: Page):
        """ Проверяем, удалось ли открыть страницу с продуктом """
        if await page.query_selector('div.content404'):
            logger.info(f'Не найдена страница: {url}')
            raise ProductNotFound


async def main():
    scraper = WildberriesProductScrapper()

    logger.info('Инициализация скраппера Wildberries прошла успешно')
    await scraper.init()
    product_url = 'https://www.wildberries.ru/catalog/149751046/detail.aspx'

    res = await scraper.get_product_description(url=product_url)
    print(f'Result: {res}')

if __name__ == '__main__':
    asyncio.run(main())
