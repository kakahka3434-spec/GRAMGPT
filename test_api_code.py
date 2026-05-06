#!/usr/bin/env python3
"""
Тест кода API без запуска сервера.
Проверяем что заглушки заменены на реальные вызовы модулей.
"""

import sys
import os
sys.path.insert(0, r'c:\Users\Administrator\Desktop\ai\GPTGRAM')

def check_code(file_path: str, checks: list) -> list:
    """Проверяет что в файле нет хардкод строк."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    results = []
    for desc, stub_pattern, should_exist in checks:
        found = stub_pattern in content
        if should_exist:
            # Проверяем что реальный код есть
            ok = found
        else:
            # Проверяем что заглушки удалены
            ok = not found
        results.append((desc, ok, f"Pattern: {stub_pattern}"))
    return results

def main():
    print("=" * 70)
    print("GRAMGPT API CODE AUDIT")
    print("=" * 70)
    
    all_results = []
    
    # 1. Проверяем analytics/summary
    print("\n📊 Checking /api/v1/analytics/summary")
    results = check_code(
        r'c:\Users\Administrator\Desktop\ai\GPTGRAM\src\api\main.py',
        [
            ("Нет хардкода 12", '"active_accounts": 12', False),
            ("Есть вызов AccountPool", 'AccountPool()', True),
            ("Есть вызов list_accounts", 'pool.list_accounts()', True),
            ("Есть вызов get_health_report", 'get_health_report()', True),
        ]
    )
    all_results.extend(results)
    for desc, ok, details in results:
        print(f"{'✅' if ok else '❌'} {desc}")
    
    # 2. Проверяем parsing/start
    print("\n🔍 Checking /api/v1/parsing/start")
    results = check_code(
        r'c:\Users\Administrator\Desktop\ai\GPTGRAM\src\api\main.py',
        [
            ("Нет хардкода parse_001", '"parse_001"', False),
            ("Есть генерация uuid task_id", 'uuid.uuid4()', True),
            ("Есть SQLite tasks table", 'CREATE TABLE IF NOT EXISTS tasks', True),
            ("Есть вызов ChannelDiscovery", 'ChannelDiscovery(telegram)', True),
            ("Есть вызов search_by_keywords", 'search_by_keywords', True),
            ("Есть проверка credentials", 'telegram_api_id', True),
        ]
    )
    all_results.extend(results)
    for desc, ok, details in results:
        print(f"{'✅' if ok else '❌'} {desc}")
    
    # 3. Проверяем parsing/results
    print("\n📋 Checking /api/v1/parsing/results/{task_id}")
    results = check_code(
        r'c:\Users\Administrator\Desktop\ai\GPTGRAM\src\api\main.py',
        [
            ("Нет хардкода Иван Петров", '"@ivanpetrov"', False),
            ("Нет хардкода Мария Иванова", '"@mivanova"', False),
            ("Есть чтение из SQLite", 'SELECT status, results FROM tasks', True),
            ("Есть json.loads", 'json.loads(results_json)', True),
        ]
    )
    all_results.extend(results)
    for desc, ok, details in results:
        print(f"{'✅' if ok else '❌'} {desc}")
    
    # 4. Проверяем commenting/start
    print("\n💬 Checking /api/v1/commenting/start")
    results = check_code(
        r'c:\Users\Administrator\Desktop\ai\GPTGRAM\src\api\main.py',
        [
            ("Нет хардкода status: active", '"status": "active"', False),
            ("Есть вызов PipelineOrchestrator", 'PipelineOrchestrator(', True),
            ("Есть вызов orchestrator.start", 'orchestrator.start', True),
            ("Есть session_id", 'session_id', True),
            ("Есть проверка is_running", '.is_running', True),
        ]
    )
    all_results.extend(results)
    for desc, ok, details in results:
        print(f"{'✅' if ok else '❌'} {desc}")
    
    # 5. Проверяем crisis/report
    print("\n🚨 Checking /api/v1/crisis/report")
    results = check_code(
        r'c:\Users\Administrator\Desktop\ai\GPTGRAM\src\api\main.py',
        [
            ("Есть endpoint /api/v1/crisis/report", '@app.post("/api/v1/crisis/report")', True),
            ("Есть CrisisReportRequest model", 'class CrisisReportRequest', True),
            ("Есть вызов crisis_manager.detect_crisis", 'crisis_manager.detect_crisis', True),
            ("Есть запись в SQLite incidents", 'CREATE TABLE IF NOT EXISTS incidents', True),
            ("Есть action_taken в response", '"action_taken"', True),
        ]
    )
    all_results.extend(results)
    for desc, ok, details in results:
        print(f"{'✅' if ok else '❌'} {desc}")
    
    # 6. Проверяем accounts
    print("\n👥 Checking /api/v1/accounts")
    results = check_code(
        r'c:\Users\Administrator\Desktop\ai\GPTGRAM\src\api\main.py',
        [
            ("Нет хардкода +7 (999) 123-45-67", '"+7 (999) 123-45-67"', False),
            ("Есть вызов AccountPool", 'pool = AccountPool()', True),
            ("Есть возврат accounts list", '"accounts": accounts', True),
        ]
    )
    all_results.extend(results)
    for desc, ok, details in results:
        print(f"{'✅' if ok else '❌'} {desc}")
    
    # Итог
    print("\n" + "=" * 70)
    print("📊 FINAL RESULTS")
    print("=" * 70)
    
    real_count = sum(1 for _, ok, _ in all_results if ok)
    stub_count = sum(1 for _, ok, _ in all_results if not ok)
    
    print(f"✅ REAL code patterns: {real_count}")
    print(f"❌ STUB patterns: {stub_count}")
    print(f"📊 Total checks: {len(all_results)}")
    
    if stub_count == 0:
        print("\n🎉 FastAPI Backend: REAL")
        print("All stub patterns replaced with real module calls.")
        return 0
    else:
        print("\n⚠️  Some patterns still indicate stubs:")
        for desc, ok, details in all_results:
            if not ok:
                print(f"   ❌ {desc}: {details}")
        print("\n⚠️  FastAPI Backend: PARTIAL")
        return 1

if __name__ == "__main__":
    sys.exit(main())
