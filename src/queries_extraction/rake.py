from nltk.corpus import stopwords
from rake_nltk import Rake
from typing import List
from loguru import logger
import re


class RAKEQueryExtractor:
    """
    Класс для составления потенциальных запросов поиска товаров на основе его описания
    """

    def __init__(self):
        self.MAX_OUTPUT_PHRASES = 5
        self.MIN_PHRASE_LENGTH = 2
        self.MAX_PHRASE_LENGTH = 5

        self.rake = Rake(
            stopwords=stopwords.words('russian'),
            min_length=self.MIN_PHRASE_LENGTH,
            max_length=self.MAX_PHRASE_LENGTH,
        )

    def extract_query_from_description(self, description: str) -> List[str]:
        """ Извлечение потенциальных поисковых запросы из описания товара.

        :param description: Текстовое описание товара
        :return: Список очищенных поисковых запросов (не более max_phrases)
        """
        phrases = self._extract_key_phrases(text=description)
        return self._clean_and_normalize_phrases(phrases=phrases)

    def _extract_key_phrases(self, text: str) -> List[str]:
        """ Извлечение ключевых фразы из текста с помощью RAKE."""

        self.rake.extract_keywords_from_text(text)
        return self.rake.get_ranked_phrases()[:self.MAX_OUTPUT_PHRASES]

    def _clean_and_normalize_phrases(self, phrases: List[str]) -> List[str]:
        """ Очистка и нормализация списка фраз """

        return [self.__clean_text(phrase).lower() for phrase in phrases]

    @staticmethod
    def __clean_text(text: str) -> str:
        """
        * Удаляем любой не буква-символьный знак перед пробелом
        * Делаем из последовательности пробелов один
        """

        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text


def main():
    queries = RAKEQueryExtractor().extract_query_from_description(
        '''Высококачественные матрасы от компании Sonox гарантируют здоровый и крепкий сон, предназначены для 
        полноценного расслабления и снятия усталости.  Двухсторонняя модель Mega Plus Foam – беспружинный матрас 
        повышенной жесткости с ортопедическим эффектом и съемным чехлом. Размер 160х200 см. Выдерживает регулярную 
        нагрузку до 320 кг без проминания и деформации. Мультизональный профиль на поверхности матраса сонокс создает 
        7 зон разной жесткости. В области плеч матрас менее жесткий, чтобы исключить излишнее давление на плечи и 
        исключить затекание конечностей. В области таза – средней жесткости, чтобы обеспечить поддержку и предотвратить 
        излишнее давление или ощущение проваливания Усиленная жесткость и упругость по всей площади спального места 
        обеспечивает точечную поддержку тела с учетом анатомических и ортопедических особенностей человека. 
        '''
    )

    logger.info("Сгенерированные поисковые запросы:")
    for i, query in enumerate(queries, 1):
        logger.info(f"{i}. {query}")


if __name__ == '__main__':
    main()
