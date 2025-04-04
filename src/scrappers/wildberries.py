import asyncio
from playwright.async_api import async_playwright
from loguru import logger
from playwright.async_api import Playwright, Browser, BrowserContext, Page


class WildberriesProductScrapper:
    def __init__(self) -> None:
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

        logger.info('Начата скраппера Wildberries прошла успешно')

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

        button_description_selector = 'button.j-details-btn-desktop'
        section_description_selector = 'section.product-details__description p.option__text'

        logger.info(f'Начинаю поиск товара с url: {url}')
        await self._page.goto(url, wait_until='networkidle')

        logger.info(f'Ожидаем появление кнопки "Характеристики и описание" для товара с url: {url}')
        await self._page.wait_for_selector(button_description_selector)

        logger.info(f'Загружается кнопка получения дополнительной информации для товара с url: {url}!')
        await self._page.click(button_description_selector)
        await self._page.wait_for_selector(section_description_selector)

        logger.info(f'Описание товара загрузилось!')
        description_content = await (await self._page.query_selector(section_description_selector)).text_content()

        logger.info(f'Найдено описание товара для товара с url: {url}:\n {description_content}')
        return description_content


if __name__ == '__main__':
    asyncio.run(WildberriesProductScrapper().init())
