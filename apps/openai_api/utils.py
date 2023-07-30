import logging
import re
from logging import Logger

_logger: Logger = logging.getLogger(name=__name__)


class ResponseFormatter:
    @classmethod
    def retrieve_list_from_string(cls, text_response: str) -> list[str]:
        listed_keywords = []
        pattern = re.compile(r"\[([^\[\]]+)\]")
        match = pattern.search(text_response)
        if match:
            listed_keywords = [s.strip().strip("\"'") for s in match.group(1).split(",")]
        else:
            _logger.warning(f"No keywords found in response: {text_response}")

        return listed_keywords
