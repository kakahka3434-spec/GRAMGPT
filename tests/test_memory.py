import pytest
from src.utils.memory import ConversationMemory

def test_memory_add_get():
    memory = ConversationMemory(limit=2)
    chat_id = 123

    memory.add_message(chat_id, "user", "Hello")
    memory.add_message(chat_id, "assistant", "Hi there")

    history = memory.get_history(chat_id)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"

def test_memory_limit():
    memory = ConversationMemory(limit=2)
    chat_id = 123

    memory.add_message(chat_id, "user", "Msg 1")
    memory.add_message(chat_id, "assistant", "Msg 2")
    memory.add_message(chat_id, "user", "Msg 3")

    history = memory.get_history(chat_id)
    assert len(history) == 2
    assert history[0]["content"] == "Msg 2"
    assert history[1]["content"] == "Msg 3"

def test_memory_clear():
    memory = ConversationMemory()
    chat_id = 123
    memory.add_message(chat_id, "user", "Hello")
    memory.clear_history(chat_id)
    assert len(memory.get_history(chat_id)) == 0
