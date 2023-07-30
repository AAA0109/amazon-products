from apps.openai_api.chat_gpt_adapter import ChatGPTAdapter
from apps.openai_api.constants import ChatRole
from apps.openai_api.entities import Message
from apps.openai_api.utils import ResponseFormatter


class AvatarDescriptionFilter:
    @classmethod
    def filter(cls, avatar_description: str, book_title: str, keywords_to_filter: list[str]) -> list[str]:
        """Removes irrelevant entries from list of keywords to advertise book titled
            and output the result as python list only.

        Args:
            avatar_description (str): book description.
            book_title (str): book title.
            keywords_to_filter (list[str]): keywords to filter.

        Returns:
            list[str]: filtered list of keywords with only relevant keywords.
        """
        prompt: str = f"remove irrelevant entries from list of keywords to advertise book titled {book_title} \
            and output the result as a Python list only (pretend you are a console interface). \
            Consider the following target reader description when deciding which \
            keywords to remove: {avatar_description}. Keywords: {str(keywords_to_filter)}"
        messages = (
            Message(role=str(ChatRole.USER), content=prompt),
            Message(role=str(ChatRole.SYSTEM), content=str(ChatRole.ADVERTIZING_BOT)),
        )
        text_response: str = ChatGPTAdapter.chat(messages)
        return cls._format_response(text_response=text_response)

    @classmethod
    def _format_response(cls, text_response: str) -> list[str]:
        return ResponseFormatter.retrieve_list_from_string(text_response=text_response)
