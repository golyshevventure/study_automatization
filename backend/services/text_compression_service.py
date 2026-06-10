"""Сервис сжатия текста с помощью sumy LexRank."""

import logging

from sumy.nlp.tokenizers import Tokenizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.lex_rank import LexRankSummarizer

logger = logging.getLogger(__name__)


class TextCompressionService:
    """Сжимает длинный текст, оставляя наиболее важные предложения."""

    @staticmethod
    def compress(text: str, sentences_count: int = 10) -> str:
        """
        Сжимает текст алгоритмом LexRank.

        При ошибке sumy или если текст слишком короткий —
        возвращает первые 8000 символов.
        """
        if not text or len(text) < 200:
            return text

        try:
            parser = PlaintextParser.from_string(text, Tokenizer("russian"))
            summarizer = LexRankSummarizer()
            summary_sentences = summarizer(parser.document, sentences_count)
            result = " ".join(str(s) for s in summary_sentences)
            return result if result else text[:8000]
        except Exception as exc:
            logger.warning("Sumy compression failed: %s", exc)
            return text[:8000]
