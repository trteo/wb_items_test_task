from loguru import logger
from playwright.async_api import Playwright, Browser, BrowserContext, Page
from playwright.async_api import async_playwright


class WildberriesBaseScrapper:
    def __init__(self) -> None:
        self._playwright: Playwright = None
        self._browser: Browser = None
        self._context: BrowserContext = None

    async def init(self) -> None:
        """ Инициализация скраппера """
        logger.info('Начата инициализация скраппера Wildberries')

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)
        self._context = await self._browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0',
        )

    async def _create_page(self) -> Page:
        """ Создаем новую страницу для запросов """
        return await self._context.new_page()

    async def close(self) -> None:
        """ Закрытие всех ресурсов скраппера """

        if self._playwright:
            await self._playwright.stop()
        self._context = None
        self._browser = None

    async def _ensure_browser_initialized(self) -> None:
        """ Проверка инициализации браузера """
        if not self._browser:
            await self.init()
