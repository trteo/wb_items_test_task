import asyncio
from typing import Union, List, Dict

from playwright.async_api import async_playwright
from loguru import logger
from playwright.async_api import Playwright, Browser, BrowserContext, Page

from src.scrappers.exceptions import PageOutOfRangeError
from src.scrappers.models import ProductPosition


class WildberriesProductScrapper:
    def __init__(self) -> None:
        self.MAX_N_PAGES_TO_SEARCH = 10

        self._playwright: Playwright = None
        self._browser: Browser = None
        self._context: BrowserContext = None
        self._page: Page = None

    async def init(self) -> None:
        """ Инициализация скраппера """
        logger.info('Начата инициализация скраппера Wildberries')

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)
        self._context = await self._browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0',
        )
        self._page = await self._context.new_page()

        logger.info('Инициализация скраппера Wildberries прошла успешно')
        res = await self.find_product_positions(1,2)
        print(f'Result: {res}')

    async def close(self) -> None:
        """ Закрытие всех ресурсов скраппера """
        if self._playwright:
            await self._playwright.stop()
        self._page = None
        self._context = None
        self._browser = None

    async def get_product_description(self, url: str) -> str:
        """
        Получение описания товара по ссылке

        Args:
            url: ссылка на товар на Wildberries

        Returns:
            Строка содержащая описание товара
        """
        if not self._page:
            await self.init()

        button_description_selector = 'button.j-details-btn-desktop'
        section_description_selector = 'section.product-details__description p.option__text'

        try:
            logger.info(f'Начинаю поиск товара с url: {url}')
            await self._page.goto(url, wait_until='networkidle')

            # TODO райзить специализированную ошибку если страница не нашлась. В эксепшене создать и в боте ловить
            logger.info(f'Ожидаем появление кнопки "Характеристики и описание" для товара с url: {url}')
            await self._page.wait_for_selector(button_description_selector)

            logger.info(f'Загружается кнопка получения дополнительной информации для товара с url: {url}!')
            await self._page.click(button_description_selector)
            await self._page.wait_for_selector(section_description_selector)

            logger.info(f'Описание товара загрузилось!')
            description_content = await (await self._page.query_selector(section_description_selector)).text_content()

            logger.info(f'Найдено описание товара для товара с url: {url}:\n {description_content}')
            return description_content
        except Exception as e:
            logger.error(f'Ошибка при попытке получить описание товара по ссылке {url}: {e}')
            raise e

    async def find_product_positions(
            self,
            product_url: str,
            queries: List[str],
    ) -> Dict[str, Union[ProductPosition, None]]:
        """
        Получаем ссылку, которую хотим найти и список запросов

        Отвечаем на сообщение набором запросов со статусом в поиске

        Для каждого запроса запускаем обход отдельно
        Каждый запрос проверяет наличие ссылки до 10 страницы (или раньше если страницы кончились)

        Если на какой то странице нашел - свою строку заменяет на `№ страницы`, `№ позиции на`, `Ссылка на страницу`
        Если дошел до конца и не нашел - свою строку заменяет на не найдено
        Если в процессе случилась ошибка - свою строку заменяет на произошла ошибка

        # :param product_url:
        # :param queries:
        # :return:
        """

        # format search page
        # scroll to page down
        # try to find
        # return page, position
        ...
        product_url = 'https://www.wildberries.ru/catalog/26231899/detail.aspx'
        queries = ['dison фен original']
        if not self._page:
            await self.init()

        result = dict()
        for query in queries:
            logger.info(f'Начинаю поиск товара по запросу: {query}')

            # Заменяем в запросе пробелы на плюсы и готовим ссылку, в которой будем подставлять номера страниц
            search_page_template_url = (
                    'https://www.wildberries.ru/catalog/0/search.aspx?'
                    'page={page_number}&sort=popular&search=' + query.replace(' ', '+')
            )

            # Проходимся по страницам, пока не найдем товар или не дойдем до установленного максимума
            result[query] = await self.__iterate_through_pages(
                search_page_template_url=search_page_template_url,
                product_url=product_url
            )
            if result[query] is None:
                logger.info(f'Товар {product_url} не найден на первых {self.MAX_N_PAGES_TO_SEARCH} страницах')

        return result

    async def __iterate_through_pages(
            self,
            search_page_template_url: str,
            product_url: str
    ) -> Union[ProductPosition, None]:
        for page in range(1, self.MAX_N_PAGES_TO_SEARCH):
            # Формируем ссылку на страницу каталога
            search_page_url = search_page_template_url.format(page_number=page)
            logger.info(f'Сканирую страницу: {search_page_url}')

            # Пытаемся найти товар на этой странице
            try:
                result = await self.__check_for_product_on_page(search_page_url=search_page_url, product_url=product_url)
            except PageOutOfRangeError:
                logger
                return

            if result:
                logger.info(f'Товар найден на странице {page}, позиции {result}')
                return ProductPosition(page_number=page, position_on_page=result)
        return

    async def __check_for_product_on_page(
            self,
            search_page_url: str,
            product_url: str
    ) -> Union[int, None]:
        logger.debug(f'Заходим на страницу {search_page_url}')
        try:
            await self._page.goto(search_page_url, wait_until='domcontentloaded')
            await self._page.wait_for_selector('div.catalog-page:not(.hide)')

            await self.__check_for_no_result(page_url=search_page_url)
        except PageOutOfRangeError as e:
            raise e

        logger.debug(f'Зашли на страницу {search_page_url}')
        await self.__scroll_page_to_the_end()

        catalog = await self._page.query_selector('div.product-card-overflow')
        product_cards = await catalog.query_selector_all('a.product-card__link')
        logger.debug(f'Found {len(product_cards)} cards')

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
        Проверяем, есть ли на странице товары

        :param page_url: ссылка на страницу для логов
        :raises PageOutOfRangeError: Если на странице нет товаров
        """
        if await self._page.query_selector('div.catalog-page__not-found'):
            logger.info(f'На странице {page_url} ничего не нашлось')
            raise PageOutOfRangeError

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


asyncio.run(WildberriesProductScrapper().init())
