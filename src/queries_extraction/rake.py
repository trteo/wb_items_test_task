from nltk.corpus import stopwords
from rake_nltk import Rake
from typing import List
import re


class RAKEQueryExtractor:
    """
    Класс для составления потенциальных запросов поиска товаров на основе его описания
    """

    def __init__(self):
        self.rake = Rake(
            stopwords=stopwords.words('russian'),
            min_length=4,  # TODO take from settings
            max_length=5,  # TODO take from settings
        )

    def extract_query_from_description(self, description: str) -> List[str]:
        """ Находим вероятные запросы на основании полученного описания """
        max_phrases = 10  # TODO take from settings

        self.rake.extract_keywords_from_text(description)
        phrases = self.rake.get_ranked_phrases()[:max_phrases]

        # TODO вынести в отдельный метод
        # Очистка и формирование запросов
        queries = []
        for phrase in phrases:
            clean_phrase = self.__clean_text(phrase)
            queries.append(clean_phrase.lower())

        return queries

    @staticmethod
    def __clean_text(text: str) -> str:
        """
        * Удаляем любой не буква-символьный знак перед пробелом
        * Делаем из последовательности пробелов один
        """

        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
