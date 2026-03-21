"""Utility & helper functions."""

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage


def get_message_text(msg: BaseMessage) -> str:
    """Get the text content of a message."""
    content = msg.content
    if isinstance(content, str):
        return content
    elif isinstance(content, dict):
        return content.get("text", "")
    else:
        txts = [c if isinstance(c, str) else (c.get("text") or "") for c in content]
        return "".join(txts).strip()


def load_chat_model(fully_specified_name: str, ollama_base_url: str | None = None) -> BaseChatModel:
    """Load a chat model from a fully specified name.

    Args:
        fully_specified_name (str): String in the format 'provider/model'.
        ollama_base_url (str | None): Base URL for Ollama, used when provider is 'ollama'.
    """
    provider, model = fully_specified_name.split("/", maxsplit=1)
    kwargs: dict = {"model_provider": provider}
    if provider == "ollama" and ollama_base_url:
        kwargs["base_url"] = ollama_base_url
    return init_chat_model(model, **kwargs)
