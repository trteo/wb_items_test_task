import asyncio
from typing import Union, List, Dict

from loguru import logger
from playwright.async_api import ElementHandle

from src.scrappers.exceptions import PageOutOfRangeError
from src.scrappers.models import ProductPosition
from src.scrappers.wildberries.wildberries_base import WildberriesBaseScrapper


class WildberriesCatalogScrapper(WildberriesBaseScrapper):
    def __init__(self) -> None:
        super().__init__()
        self.MAX_N_PAGES_TO_SEARCH = 10

    async def find_product_positions(
            self,
            product_url: str,
            queries: List[str],
    ) -> Dict[str, Union[ProductPosition, None]]:
        """
        Ищет позицию товара по нескольким поисковым запросам.

        Args:
            product_url: URL искомого товара
            queries: Список поисковых запросов

        Returns:
            Словарь с результатами поиска для каждого запроса
        """
        await self._ensure_browser_initialized()
        return await self.__search_product_by_all_queries(product_url, queries)

    async def __search_product_by_all_queries(
            self,
            product_url: str,
            queries: List[str]
    ) -> Dict[str, Union[ProductPosition, None]]:
        """ Организация поиска товара по всем запросам """
        results = {}

        for query in queries:
            logger.info(f'Начинаю поиск товара по запросу: {query}')
            search_url = self.__build_search_url(query)
            results[query] = await self.__search_product_by_query(search_url, product_url)

        return results

    @staticmethod
    def __build_search_url(query: str) -> str:
        """Формирует URL для поиска по заданному запросу."""
        return (
                'https://www.wildberries.ru/catalog/0/search.aspx?'
                'page={page_number}&sort=popular&search=' + query.replace(' ', '+')
        )

    async def __search_product_by_query(
            self,
            search_page_template_url: str,
            product_url: str
    ) -> Union[ProductPosition, None]:
        """ Поиск товара по одному запросу """

        result = await self.__iterate_through_pages(
            search_page_template_url=search_page_template_url,
            product_url=product_url
        )

        if result is None:
            logger.info(f'Товар {product_url} не найден на первых {self.MAX_N_PAGES_TO_SEARCH} страницах')

        return result

    async def __iterate_through_pages(
            self,
            search_page_template_url: str,
            product_url: str
    ) -> Union[ProductPosition, None]:
        """Итерируется по страницам поиска, пока не найдет товар или не достигнет предела."""

        for page in range(1, self.MAX_N_PAGES_TO_SEARCH):
            search_page_url = search_page_template_url.format(page_number=page)
            logger.info(f'Сканирую страницу: {search_page_url}')

            try:
                if position := await self.__check_for_product_on_page(
                        search_page_url=search_page_url,
                        product_url=product_url
                ):
                    logger.info(f'Товар найден на странице {page}, позиции {position}')
                    return ProductPosition(page_number=page, position_on_page=position, page_url=search_page_url)

            except PageOutOfRangeError:
                break

        return None

    async def __check_for_product_on_page(
            self,
            search_page_url: str,
            product_url: str
    ) -> Union[int, None]:
        """Проверяет наличие продукта на странице поиска и возвращает его позицию."""
        await self.__navigate_to_search_page(search_page_url)
        product_cards = await self.__get_product_cards_from_page()
        return await self.__find_product_position(product_cards, product_url)

    async def __navigate_to_search_page(self, search_page_url: str) -> None:
        """Переходит на страницу поиска и дожидается её загрузки."""
        logger.debug(f'Заходим на страницу {search_page_url}')
        try:
            await self._page.goto(search_page_url, wait_until='domcontentloaded')
            await self._page.wait_for_selector('div.catalog-page:not(.hide)')
            await self.__check_for_no_result(page_url=search_page_url)
        except PageOutOfRangeError as e:
            raise e
        logger.debug(f'Зашли на страницу {search_page_url}')
        await self.__scroll_page_to_the_end()

    async def __get_product_cards_from_page(self) -> List[ElementHandle]:
        """Получает все карточки продуктов со страницы."""
        catalog = await self._page.query_selector('div.product-card-overflow')
        product_cards = await catalog.query_selector_all('a.product-card__link')
        logger.debug(f'Found {len(product_cards)} cards')

        return product_cards

    @staticmethod
    async def __find_product_position(
            product_cards: List[ElementHandle],
            product_url: str
    ) -> Union[int, None]:
        """Ищет продукт среди карточек и возвращает его позицию."""
        for index, card in enumerate(product_cards, 1):
            href = await card.get_attribute('href')
            logger.debug(f'Found href {href}')
            if not href:
                continue
            if product_url == href:
                return index
        return None

    async def __check_for_no_result(self, page_url: str) -> None:
        """
        Проверяем, есть ли на странице товары. Встретил два типа страниц без товаров

        :param page_url: ссылка на страницу для логов
        :raises PageOutOfRangeError: Если на странице нет товаров
        """
        # Проверка случая когда просто говорит что ничего не нашел
        if await self._page.query_selector('div.catalog-page__not-found'):
            logger.info(f'На странице {page_url} ничего не нашлось')
            raise PageOutOfRangeError

        # Проверка случая, когда предлагает товары по похожему запросу
        searching_result_text = await self._page.query_selector('p.searching-results__text:not(.hide)')
        if searching_result_text and 'ничего не нашлось' in await searching_result_text.text_content():
            logger.info(f'На странице {page_url} ничего не нашлось')
            raise PageOutOfRangeError

    async def __scroll_page_to_the_end(self):
        """
        Функция проматывает страницу до конца что бы загрузить все товары
        """

        viewport_height = await self._page.evaluate("window.innerHeight")
        current_position = 0
        last_height = await self._page.evaluate("document.body.scrollHeight")

        logger.info('Листаю страницу вниз')
        while current_position < last_height:
            # Скролим на 80% страницы, что бы часть старого контента осталось
            current_position += viewport_height * 0.8
            await self._page.evaluate(f"window.scrollTo(0, {current_position})")

            # Ждем подгрузки товаров
            await asyncio.sleep(1)

            # Проверяем, дошли ли мы до конца страницы
            new_height = await self._page.evaluate("document.body.scrollHeight")
            if new_height > last_height:
                last_height = new_height

        logger.info('Страница пролистана')


async def main():
    scraper = WildberriesCatalogScrapper()

    logger.info('Инициализация скраппера Wildberries прошла успешно')
    await scraper.init()
    product_url = 'https://www.wildberries.ru/catalog/149751046/detail.aspx'
    queries = ['зонт мужской автомат', 'зонт мужской']

    res = await scraper.find_product_positions(product_url=product_url, queries=queries)
    print(f'Result: {res}')

if __name__ == '__main__':
    asyncio.run(main())
