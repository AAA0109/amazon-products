import openai

from .entities import Message


class ChatGPTAdapter:
    MODEL = "gpt-4"

    @classmethod
    def chat(cls, messages: tuple[Message, ...], **kwargs) -> str:
        temperature: float = kwargs.get("temperature", 1.0)
        top_p: float = kwargs.get("top_p", 1.0)

        response = openai.ChatCompletion.create(
            model=cls.MODEL,
            messages=[message.to_dict() for message in messages],
            temperature=temperature,
            top_p=top_p,
        )
        text: str = response["choices"][0]["message"]["content"]
        return text
