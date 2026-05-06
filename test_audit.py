#!/usr/bin/env python3
"""Автотест для проверки всех модулей GRAMGPT."""

import sys
import os
sys.path.insert(0, r'c:\Users\Administrator\Desktop\ai\GPTGRAM')

from unittest.mock import Mock, AsyncMock, patch
import asyncio

# Test results
results = []

def check(desc, condition, file_line=""):
    status = "✅ PASS" if condition else "❌ FAIL"
    results.append((desc, condition, file_line))
    print(f"{status}: {desc} [{file_line}]")
    return condition

async def run_tests():
    print("=" * 70)
    print("GRAMGPT AUDIT TEST SUITE")
    print("=" * 70)
    
    # === ИМПОРТЫ ===
    print("\n📦 ИМПОРТЫ МОДУЛЕЙ")
    
    try:
        from src.services.channel_discovery import ChannelDiscovery
        check("ChannelDiscovery import", True, "channel_discovery.py:1")
    except Exception as e:
        check("ChannelDiscovery import", False, f"ERROR: {e}")
    
    try:
        from src.services.comment_sniper import CommentSniper
        check("CommentSniper import", True, "comment_sniper.py:1")
    except Exception as e:
        check("CommentSniper import", False, f"ERROR: {e}")
    
    try:
        from src.services.promo_engine import PromoEngine
        check("PromoEngine import", True, "promo_engine.py:1")
    except Exception as e:
        check("PromoEngine import", False, f"ERROR: {e}")
    
    try:
        from src.core.work_modes import WorkModeController
        check("WorkModeController import", True, "work_modes.py:1")
    except Exception as e:
        check("WorkModeController import", False, f"ERROR: {e}")
    
    try:
        from src.core.pipeline_orchestrator import PipelineOrchestrator
        check("PipelineOrchestrator import", True, "pipeline_orchestrator.py:1")
    except Exception as e:
        check("PipelineOrchestrator import", False, f"ERROR: {e}")
    
    try:
        from src.core.neuro_modules import neuro_commenting
        check("NeuroModules import", True, "neuro_modules.py:1")
    except Exception as e:
        check("NeuroModules import", False, f"ERROR: {e}")
    
    try:
        from src.core.human_emulation import human_engine
        check("HumanEmulation import", True, "human_emulation.py:1")
    except Exception as e:
        check("HumanEmulation import", False, f"ERROR: {e}")
    
    try:
        from src.core.fingerprint import fp_engine
        check("FingerprintEngine import", True, "fingerprint.py:1")
    except Exception as e:
        check("FingerprintEngine import", False, f"ERROR: {e}")
    
    try:
        from src.core.crisis_manager import crisis_manager
        check("CrisisManager import", True, "crisis_manager.py:1")
    except Exception as e:
        check("CrisisManager import", False, f"ERROR: {e}")
    
    try:
        from src.core.router import channel_router
        check("MultiChannelRouter import", True, "router.py:1")
    except Exception as e:
        check("MultiChannelRouter import", False, f"ERROR: {e}")
    
    try:
        from src.core.autofunnel import autofunnel
        check("Autofunnel import", True, "autofunnel.py:1")
    except Exception as e:
        check("Autofunnel import", False, f"ERROR: {e}")
    
    # === СТРУКТУРНЫЕ ПРОВЕРКИ ===
    print("\n🔍 СТРУКТУРНЫЕ ПРОВЕРКИ")
    
    # Check ChannelDiscovery methods
    try:
        from src.services.channel_discovery import ChannelDiscovery
        methods = ['search_by_keywords', 'filter_open_comments', 'discover_target_channels']
        for m in methods:
            check(f"ChannelDiscovery.{m}", hasattr(ChannelDiscovery, m), f"channel_discovery.py")
    except:
        pass
    
    # Check CommentSniper methods
    try:
        from src.services.comment_sniper import CommentSniper
        methods = ['start_monitoring', 'stop_monitoring', '_on_new_message', '_edit_worker']
        for m in methods:
            check(f"CommentSniper.{m}", hasattr(CommentSniper, m), f"comment_sniper.py")
    except:
        pass
    
    # Check WorkModeController methods
    try:
        from src.core.work_modes import WorkModeController
        controller = WorkModeController("balanced")
        check("WorkModeController.switch_mode", hasattr(controller, 'switch_mode'), "work_modes.py:101")
        check("WorkModeController.auto_downgrade", hasattr(controller, 'auto_downgrade'), "work_modes.py:137")
        
        # Test auto_downgrade logic
        controller2 = WorkModeController("aggressive")
        downgraded = controller2.auto_downgrade(0.8)  # risk > 0.7 threshold
        check("auto_downgrade logic works", downgraded and controller2.current_mode == "balanced", "work_modes.py:137")
    except Exception as e:
        check("WorkModeController tests", False, f"ERROR: {e}")
    
    # Check PromoEngine methods
    try:
        from src.services.promo_engine import PromoEngine
        engine = PromoEngine({})
        check("PromoEngine.validate_comment", hasattr(engine, 'validate_comment'), "promo_engine.py:269")
        check("PromoEngine._calculate_spam_score", hasattr(engine, '_calculate_spam_score'), "promo_engine.py:216")
        
        # Test spam scoring
        spam_text = "FREE MONEY!!! CLICK HERE NOW!!!"
        validation = engine.validate_comment(spam_text, "balanced")
        check("Spam detection works (high spam rejected)", not validation["valid"], "promo_engine.py:216")
        
        safe_text = "Интересный пост, спасибо за информацию"
        validation2 = engine.validate_comment(safe_text, "balanced")
        check("Safe text passes validation", validation2["valid"], "promo_engine.py:269")
    except Exception as e:
        check("PromoEngine tests", False, f"ERROR: {e}")
    
    # === MOCK API ТЕСТЫ ===
    print("\n🌐 API ENDPOINTS (MOCK CHECK)")
    
    # Check if endpoints exist (even if stub)
    try:
        from src.api.main import app
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        check("/api/v1/status exists", "/api/v1/status" in routes, "api/main.py:31")
        check("/api/v1/analytics/summary exists", "/api/v1/analytics/summary" in routes, "api/main.py:40")
        check("/api/v1/campaigns/create exists", "/api/v1/campaigns/create" in routes, "api/main.py:35")
        check("/api/v1/parsing/start exists", "/api/v1/parsing/start" in routes, "api/main.py:80")
        check("/api/v1/commenting/start exists", "/api/v1/commenting/start" in routes, "api/main.py:113")
    except Exception as e:
        check("API routes check", False, f"ERROR: {e}")
    
    # === CRISIS MANAGER ПРОБЛЕМА ===
    print("\n⚠️  ИЗВЕСТНЫЕ ПРОБЛЕМЫ")
    
    try:
        from src.core.crisis_manager import crisis_manager
        # Проверяем что нет метода получения reports
        has_report_source = hasattr(crisis_manager, 'get_account_reports') or hasattr(crisis_manager, 'report_incident')
        check("CrisisManager: источник данных о reports", has_report_source, "crisis_manager.py")
        if not has_report_source:
            print("   ⚠️  Нет источника данных о reports — модуль требует доработки")
    except Exception as e:
        check("CrisisManager check", False, f"ERROR: {e}")
    
    # === ROUTER ПРОБЛЕМА ===
    try:
        from src.core.router import channel_router
        # Проверяем что методы не делают реальных вызовов
        import inspect
        source = inspect.getsource(channel_router.route_lead)
        has_real_wa = "whatsapp" in source.lower() and ("api.whatsapp" in source.lower() or "graph.instagram" in source.lower())
        check("MultiChannelRouter: WhatsApp реальная интеграция", has_real_wa, "router.py:32")
        if not has_real_wa:
            print("   ⚠️  WhatsApp/Instagram/Email/SMS — заглушки (возвращают {'status': 'sent'} без реальной отправки)")
    except Exception as e:
        check("Router check", False, f"ERROR: {e}")
    
    # === AUTOFUNNEL ПРОБЛЕМА ===
    try:
        from src.core.autofunnel import autofunnel
        import inspect
        source = inspect.getsource(autofunnel.execute_sequence)
        # Проверяем что delay не закомментирован
        has_real_delay = "asyncio.sleep" in source and "86400" in source
        check("Autofunnel: реальные задержки (не закомментированы)", has_real_delay, "autofunnel.py:32")
        if not has_real_delay:
            print("   ⚠️  Задержки закомментированы — нужна интеграция с Celery/Redis")
    except Exception as e:
        check("Autofunnel check", False, f"ERROR: {e}")
    
    # === BOT HANDLERS ===
    print("\n🤖 BOT HANDLERS")
    
    try:
        from src.services.bot.handlers import commands, admin_pipeline, admin_analytics
        check("commands handler import", True, "bot/handlers/commands.py")
        check("admin_pipeline handler import", True, "bot/handlers/admin_pipeline.py")
        check("admin_analytics handler import", True, "bot/handlers/admin_analytics.py")
        
        # Проверяем что есть команды
        check("commands.router exists", hasattr(commands, 'router'), "commands.py:10")
        check("admin_pipeline.router exists", hasattr(admin_pipeline, 'router'), "admin_pipeline.py:22")
        check("admin_analytics.router exists", hasattr(admin_analytics, 'router'), "admin_analytics.py:20")
    except Exception as e:
        check("Bot handlers check", False, f"ERROR: {e}")
    
    # === ИТОГ ===
    print("\n" + "=" * 70)
    print("📊 ИТОГОВЫЙ РЕЗУЛЬТАТ")
    print("=" * 70)
    
    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)
    
    print(f"✅ PASS: {passed}")
    print(f"❌ FAIL: {failed}")
    print(f"📊 Всего: {len(results)}")
    
    if failed == 0:
        print("\n🎉 Все тесты пройдены!")
        return 0
    else:
        print(f"\n⚠️  {failed} тестов провалено")
        print("\n❌ FAIL детали:")
        for desc, ok, file_line in results:
            if not ok:
                print(f"   - {desc} [{file_line}]")
        
        print("\n📋 РЕКОМЕНДАЦИИ:")
        print("   1. CrisisManager: добавить report_incident() метод")
        print("   2. MultiChannelRouter: интегрировать WA/IG/Email API")
        print("   3. Autofunnel: добавить Celery для persistency")
        print("   4. FastAPI: заменить mock endpoints на real")
        
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(run_tests())
    sys.exit(exit_code)
