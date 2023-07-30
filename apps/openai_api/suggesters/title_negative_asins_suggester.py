from apps.openai_api.chat_gpt_adapter import ChatGPTAdapter
from apps.openai_api.constants import ChatRole
from apps.openai_api.entities import Message
from apps.openai_api.utils import ResponseFormatter


class TitleNegativeAsinsSuggester:
    @classmethod
    def suggest_asins(cls, book_title: str, title2asin_map: dict, negative: bool = False) -> list[str]:
        """Suggests negatives of provided negative type for a book.

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
            list[str]: list of negatives of provided negative type .
        """
        collected_asins = []
        if negative:
            type_text = "would not be interested in"
        else:
            type_text = "would be interested in"

        for content_table in cls.create_asins_table_string_from_dict(title2asin_map):
            messages = (
                Message(role=str(ChatRole.ASSISTANT), content=f"Markdown table: {content_table}"),
                Message(role=str(ChatRole.ASSISTANT), content=f"Book title: {book_title}"),
                Message(
                    role=str(ChatRole.USER),
                    content=f"Pick out all ASINs a person interested in this book {type_text}. "
                    "Ensure that all selected ASINs are found in the provided markdown table. "
                    "Note that the first column contains the ASINs "
                    "and the second column contains the book titles."
                    "Return the ASINs only as a python list.",
                ),
            )
            text_response: str = ChatGPTAdapter.chat(messages, temperature=0.1, top_p=0.1)
            collected_asins.extend(cls._format_response(text_response=text_response))

        return collected_asins

    @classmethod
    def _format_response(cls, text_response: str) -> list[str]:
        return ResponseFormatter.retrieve_list_from_string(text_response=text_response)

    @classmethod
    def create_asins_table_string_from_dict(cls, title2asin_map: dict, max_length: int = 15_000):
        lst = [[v, k] for k, v in title2asin_map.items()]
        return cls.create_asins_table_string(lst, max_length=max_length)

    @staticmethod
    def create_asins_table_string(lst: list[list[str]], max_length: int = 15_000):
        """
        Constructs a string formatted as a markdown table of ASINs (Amazon Standard Identification Numbers), which can be submitted to ChatGPT.

        The table includes a title row and individual rows for each ASIN in the input list. Each row in the table is comprised of ASINs and their corresponding titles. The table rows are yielded in strings of a maximum specified length.

        Args:
            lst (list[list[str]]): A 2D list where each sublist represents a row in the table. The first element of the sublist is assumed to be the ASIN, and the rest are assumed to be part of the Title.
            max_length (int, optional): The maximum length for each yielded string. Defaults to 20000 characters.

        Yields:
            str: A string representing a markdown formatted table, split into multiple strings if the total length exceeds the max_length. The output string(s) includes the table headers and as many rows as can fit within the max_length constraint. If the total table length exceeds max_length, the table is split into multiple strings, each containing a portion of the table and starting with the table headers.
        """
        result = []
        current_length = 0

        # Add the title row
        result.append("| ASIN | Title |")
        result.append("| --- | --- |")
        current_length += len(result[0]) + len(result[1])

        for sublst in lst:
            if not sublst[0] or not sublst[1] or sublst[0] is None or sublst[1] is None:
                continue
            asin = str(sublst[0]).upper()  # Convert ASIN to uppercase string
            sublst_str = (
                "| " + asin + " | " + " | ".join(str(item) for item in sublst[1:]) + " |"
            )  # Join the remaining elements with the delimiter
            sublst_length = len(sublst_str)

            if current_length + sublst_length <= max_length:
                result.append(sublst_str)
                current_length += sublst_length
            else:
                yield "\n".join(result)
                result = [
                    "| ASIN | Title |",
                    "| --- | --- |",
                    sublst_str,
                ]  # Start a new result list with the title row
                current_length = len(result[0]) + len(result[1]) + sublst_length

        if result:
            yield "\n".join(result)
