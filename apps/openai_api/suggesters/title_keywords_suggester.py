from typing import Optional

from apps.openai_api.chat_gpt_adapter import ChatGPTAdapter
from apps.openai_api.constants import ChatRole
from apps.openai_api.entities import Message
from apps.openai_api.utils import ResponseFormatter


class TitleKeywordsSuggester:
    @classmethod
    def suggest_keywords(
        cls,
        title: str,
        keywords_count: int = 30,
        keywords_type: str = "main",
        description: Optional[str] = None,
        language: str = "English",
        length_inequality: str = "exactly",
    ) -> list[str]:
        """Generates a list of keywords to advertise book with given title.

        Args:
            title (str): book title.
            keywords_count (int, optional): number of keywords to be suggested. Defaults to 30.
            keywords_type (str, optional): type of keywords to be suggested. Defaults to "main", also possible values: "broad", "exact" and other.
            description (str, optional): book description sould be provided if title is vague.
            language (str): keywords language
            length_inequality (str): specify "exactly" or "at least" or "at most" etc to modulate the length
        Returns:
            list[str]: the list of suggested keywords.
        """
        language = "" if language == "English" else f"in {language}"
        messages = [
            Message(role=str(ChatRole.ASSISTANT), content=f"Book title: {title}"),
            Message(role=str(ChatRole.ASSISTANT), content=f"Book description: {description}"),
            Message(
                role=str(ChatRole.USER),
                content=(
                    f"Generate {keywords_count} {keywords_type} keywords {language} to advertise this book on Amazon. "
                    f"Keywords must be {length_inequality} two words in length. "
                    f"Return a Python list only."
                ),
            ),
        ]
        if not description:
            messages.pop(1)

        text_response: str = ChatGPTAdapter.chat(tuple(messages), temperature=0.5, top_p=0.1)
        return cls._format_response(text_response=text_response)

    @classmethod
    def _format_response(cls, text_response: str) -> list[str]:
        return ResponseFormatter.retrieve_list_from_string(text_response=text_response)
