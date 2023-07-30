from apps.openai_api.chat_gpt_adapter import ChatGPTAdapter
from apps.openai_api.constants import ChatRole
from apps.openai_api.entities import Message
from apps.openai_api.utils import ResponseFormatter


class TitleAsinsSuggester:
    @classmethod
    def suggest_asins(cls, book_title: str, title2asin_map: dict, negative: bool = False) -> list[str]:
        """Suggests keywords of provided negative type for a book.

        Args:
            book_title (str): book title.
            negative (bool): type of returned asin. If False then Negative else Positive
            title2asin_map (dict): it's a map with following structure:
        ```
        {
            "The Surprising Benefits of Gardening": "FYMRAMWRP",
            "The Advantages of Owning a Pet": "EFJMNNDAMP",
            "The Science of Climate Change": "OUPTKUERSO",
        }
        ```
        Returns:
            list[str]: list of keywords of provided negative type .
        """
        collected_asins = []
        if negative:
            type_text = "would not be interested in"
        else:
            type_text = "would be interested in"

        for title2asin_map_chunk in cls.message_length_chunker(title2asin_map):
            messages = (
                Message(
                    role=str(ChatRole.ASSISTANT), content=f"ASINs dict: {title2asin_map_chunk}"
                ),
                Message(role=str(ChatRole.ASSISTANT), content=f"Book title: {book_title}"),
                Message(
                    role=str(ChatRole.USER),
                    content=f"Pick out all ASINs a person interested in this book {type_text}. "
                            "Ensure that all selected ASINs are found in the provided python dict values. "
                            "Note that keys of given dict are book titles and values are ASINs. "
                            "Return the ASINs only as a python list.",
                ),
            )
            text_response: str = ChatGPTAdapter.chat(messages, temperature=0.1, top_p=0.1)
            collected_asins.extend(cls._format_response(text_response=text_response))

        return collected_asins

    @classmethod
    def _format_response(cls, text_response: str) -> list[str]:
        return ResponseFormatter.retrieve_list_from_string(text_response=text_response)

    @staticmethod
    def message_length_chunker(title2asin_map: dict[str, str], chunk_size: int = 12_500):
        """
        Splits a given dictionary into chunks where the combined length of keys and values is less than or equal to
        the specified chunk size. Yields a dictionary for each chunk.

        Args:
            title2asin_map (dict): A dictionary of book title to ASIN mappings.
            chunk_size (int): The maximum combined length of keys and values in each chunk. Default is 12_500.

        Yields:
            dict: A dictionary containing book title to ASIN mappings for a single chunk.
        """
        curernt_size = 0
        chunk = {}
        for k, v in title2asin_map.items():
            curernt_size += len(k) + len(v)
            if curernt_size < chunk_size:
                chunk.update({k: v})
            else:
                curernt_size = 0
                yield chunk
                chunk.clear()
