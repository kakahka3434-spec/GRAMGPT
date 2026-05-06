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


def test_db_clear_history(temp_db):
    chat_id = 888
    temp_db.add_message(chat_id, "user", "Test message")
    temp_db.add_message(chat_id, "assistant", "Test response")
    assert len(temp_db.get_history(chat_id)) == 2

    temp_db.clear_history(chat_id)
    assert len(temp_db.get_history(chat_id)) == 0


def test_db_subscription(temp_db):
    chat_id = 777
    sub = temp_db.get_subscription(chat_id)
    assert sub["plan"] == "free"
    assert sub["actions"] == 100


def test_db_referral(temp_db):
    temp_db.add_referral(user_id=100, referrer_id=200)
    # Should not raise on duplicate
    temp_db.add_referral(user_id=100, referrer_id=200)


def test_db_campaign(temp_db):
    temp_db.create_campaign("Test Campaign", "Test Goal", {"predicted_roi": "200%"})
    report = temp_db.get_roi_report(1)
    assert "roi_actual" in report


def test_db_history_limit(temp_db):
    chat_id = 666
    for i in range(30):
        temp_db.add_message(chat_id, "user", f"Message {i}")

    history = temp_db.get_history(chat_id, limit=10)
    assert len(history) == 10
