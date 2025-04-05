from loguru import logger

from src.scrappers.wildberries.wildberries_base import WildberriesBaseScrapper


class WildberriesProductScrapper(WildberriesBaseScrapper):
    async def get_product_description(self, url: str) -> str:
        """
        Получение описания товара по ссылке

        :param  url: ссылка на товар на Wildberries
        :return: Строка содержащая описание товара
        """
        await self._ensure_browser_initialized()

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