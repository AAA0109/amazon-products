from enum import Enum


class ChatRole(Enum):
    BOOK_ADVERTISER = "You are a terminal interface helping a publisher advertise books on Amazon"
    ADVERTIZING_BOT = "You are an advertising bot that understands the target market well"
    BOOK_RELEVANCE_ANALYZER = (
        "You are a diligent relevance analyzer helping a publisher classify books on Amazon"
    )
    USER = "user"
    SYSTEM = "system"
    ASSISTANT = "assistant"

    def __str__(self) -> str:
        return self.value
