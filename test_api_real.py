#!/usr/bin/env python3
"""
Тест FastAPI endpoints после исправления заглушек на реальные вызовы.
Запускает сервер, делает запросы, проверяет отсутствие "Mock" и хардкод.
"""

import subprocess
import time
import requests
import sys
import json
import sqlite3
import os

BASE_URL = "http://localhost:8000"
TEST_RESULTS = []

def check(desc: str, condition: bool, details: str = ""):
    status = "✅ REAL" if condition else "❌ STUB"
    TEST_RESULTS.append((desc, condition, details))
    print(f"{status}: {desc}")
    if details and not condition:
        print(f"   Details: {details}")
    return condition

def start_server():
    """Запускает uvicorn в фоновом процессе."""
    print("🚀 Starting FastAPI server...")
    env = os.environ.copy()
    env["PYTHONPATH"] = r"c:\Users\Administrator\Desktop\ai\GPTGRAM"
    
    proc = subprocess.Popen(
        ["python", "-m", "uvicorn", "src.api.main:app", "--port", "8000", "--reload"],
        cwd=r"c:\Users\Administrator\Desktop\ai\GPTGRAM",
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    # Ждём запуска
    time.sleep(3)
    return proc

def stop_server(proc):
    """Останавливает сервер."""
    proc.terminate()
    proc.wait(timeout=5)
    print("\n🛑 Server stopped")

def test_analytics_summary():
    """Тест /api/v1/analytics/summary — проверяем что нет хардкода 12."""
    print("\n📊 Testing /api/v1/analytics/summary")
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/analytics/summary", timeout=5)
        data = resp.json()
        
        # Проверяем что active_accounts не хардкод 12
        is_real = (
            resp.status_code == 200 and
            "active_accounts" in data and
            data.get("active_accounts") != 12  # старый хардкод
        )
        
        check(
            "/api/v1/analytics/summary",
            is_real,
            f"Got: {data}" if not is_real else ""
        )
        return is_real
    except Exception as e:
        check("/api/v1/analytics/summary", False, str(e))
        return False

def test_parsing_start():
    """Тест /api/v1/parsing/start — должен вернуть реальный task_id и записать в SQLite."""
    print("\n🔍 Testing /api/v1/parsing/start")
    try:
        payload = {
            "parser_type": "keywords",
            "target": "crypto",
            "keywords": "crypto,bitcoin,eth",
            "limit": 10
        }
        resp = requests.post(f"{BASE_URL}/api/v1/parsing/start", json=payload, timeout=30)
        data = resp.json()
        
        task_id = data.get("task_id", "")
        # Проверяем что task_id не старый хардкод "parse_001"
        is_real_task_id = task_id and task_id != "parse_001" and "parse_" in task_id
        
        # Проверяем что записано в SQLite
        tasks_db = "data/tasks.db"
        in_db = False
        if os.path.exists(tasks_db):
            with sqlite3.connect(tasks_db) as conn:
                cursor = conn.execute("SELECT 1 FROM tasks WHERE task_id = ?", (task_id,))
                in_db = cursor.fetchone() is not None
        
        is_real = resp.status_code == 200 and is_real_task_id and in_db
        check(
            "/api/v1/parsing/start",
            is_real,
            f"status={resp.status_code}, task_id={task_id}, in_db={in_db}" if not is_real else ""
        )
        return task_id if is_real else None
    except Exception as e:
        check("/api/v1/parsing/start", False, str(e))
        return None

def test_parsing_results(task_id: str):
    """Тест /api/v1/parsing/results/{task_id}."""
    print(f"\n📋 Testing /api/v1/parsing/results/{task_id}")
    if not task_id:
        check("/api/v1/parsing/results", False, "No task_id provided")
        return False
    
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/parsing/results/{task_id}", timeout=5)
        data = resp.json()
        
        # Проверяем что нет хардкод списка
        results = data.get("results", [])
        is_mock = (
            len(results) > 0 and 
            results[0].get("username") == "@ivanpetrov"  # старый хардкод
        )
        
        is_real = resp.status_code == 200 and not is_mock
        check(
            "/api/v1/parsing/results/{task_id}",
            is_real,
            f"Got mock data: {results[0]}" if is_mock else ""
        )
        return is_real
    except Exception as e:
        check("/api/v1/parsing/results/{task_id}", False, str(e))
        return False

def test_accounts():
    """Тест /api/v1/accounts — должен вернуть реальные данные из AccountPool."""
    print("\n👥 Testing /api/v1/accounts")
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/accounts", timeout=5)
        data = resp.json()
        
        # Проверяем что нет хардкод данных
        accounts = data.get("accounts", [])
        is_mock = (
            len(accounts) > 0 and 
            accounts[0].get("phone") == "+7 (999) 123-45-67"  # старый хардкод
        )
        
        is_real = resp.status_code == 200 and not is_mock
        check(
            "/api/v1/accounts",
            is_real,
            f"Got mock: {accounts[0]}" if is_mock else f"Got {len(accounts)} accounts"
        )
        return is_real
    except Exception as e:
        check("/api/v1/accounts", False, str(e))
        return False

def test_crisis_report():
    """Тест /api/v1/crisis/report — должен записать инцидент и вернуть анализ."""
    print("\n🚨 Testing /api/v1/crisis/report")
    try:
        payload = {
            "account_id": "+79990000001",
            "incident_type": "flood_error",
            "details": "FloodWaitError: wait 60 seconds"
        }
        resp = requests.post(f"{BASE_URL}/api/v1/crisis/report", json=payload, timeout=10)
        data = resp.json()
        
        # Проверяем что записано в SQLite
        incidents_db = "data/incidents.db"
        in_db = False
        if os.path.exists(incidents_db):
            with sqlite3.connect(incidents_db) as conn:
                cursor = conn.execute(
                    "SELECT 1 FROM incidents WHERE account_id = ? AND type = ?",
                    ("+79990000001", "flood_error")
                )
                in_db = cursor.fetchone() is not None
        
        is_real = (
            resp.status_code == 200 and 
            "action_taken" in data and
            in_db
        )
        check(
            "/api/v1/crisis/report",
            is_real,
            f"status={resp.status_code}, in_db={in_db}, response={data}" if not is_real else ""
        )
        return is_real
    except Exception as e:
        check("/api/v1/crisis/report", False, str(e))
        return False

def main():
    print("=" * 70)
    print("GRAMGPT API REAL TEST SUITE")
    print("=" * 70)
    
    # Запускаем сервер
    server_proc = start_server()
    
    try:
        # Ждём готовности
        time.sleep(2)
        
        # Проверяем что сервер жив
        try:
            requests.get(f"{BASE_URL}/api/v1/status", timeout=5)
        except:
            print("❌ Server not responding, aborting tests")
            return 1
        
        # Запускаем тесты
        test_analytics_summary()
        task_id = test_parsing_start()
        if task_id:
            test_parsing_results(task_id)
        test_accounts()
        test_crisis_report()
        
        # Итог
        print("\n" + "=" * 70)
        print("📊 FINAL RESULTS")
        print("=" * 70)
        
        real_count = sum(1 for _, ok, _ in TEST_RESULTS if ok)
        stub_count = sum(1 for _, ok, _ in TEST_RESULTS if not ok)
        
        print(f"✅ REAL: {real_count}")
        print(f"❌ STUB: {stub_count}")
        print(f"📊 Total: {len(TEST_RESULTS)}")
        
        if stub_count == 0:
            print("\n🎉 FastAPI Backend: REAL")
            return 0
        else:
            print("\n⚠️  Some endpoints still have stubs:")
            for desc, ok, details in TEST_RESULTS:
                if not ok:
                    print(f"   ❌ {desc}: {details}")
            print("\n⚠️  FastAPI Backend: PARTIAL (some endpoints still STUB)")
            return 1
            
    finally:
        stop_server(server_proc)

if __name__ == "__main__":
    sys.exit(main())
