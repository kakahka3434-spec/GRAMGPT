import os
import pytest
from src.db.database import Database

@pytest.fixture
def temp_db():
    db_path = "test_gramgpt.db"
    db = Database(db_path)
    yield db
    if os.path.exists(db_path):
        os.remove(db_path)

def test_db_add_get_history(temp_db):
    chat_id = 999
    temp_db.add_message(chat_id, "user", "Hello")
    temp_db.add_message(chat_id, "assistant", "Hi!")

    history = temp_db.get_history(chat_id)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"

def test_db_user_settings(temp_db):
    chat_id = 999
    assert temp_db.get_user_model(chat_id) == "gpt-4o"

    temp_db.set_user_model(chat_id, "gpt-4o-mini")
    assert temp_db.get_user_model(chat_id) == "gpt-4o-mini"
