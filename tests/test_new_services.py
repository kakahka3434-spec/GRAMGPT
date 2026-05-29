"""Tests for newly implemented services: CrisisManager, AutomationEngine, AutoFunnel."""

import os
import time
import tempfile
import pytest
from src.core.crisis_manager import AICrisisManager
from src.core.automation import AutomationEngine
from src.core.autofunnel import AutoFunnelEngine


class TestCrisisManager:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.path = self.tmp.name
        self.tmp.close()
        self.cm = AICrisisManager(db_path=self.path)

    def teardown_method(self):
        try:
            os.remove(self.path)
        except PermissionError:
            time.sleep(0.1)
            try:
                os.remove(self.path)
            except PermissionError:
                pass

    @pytest.mark.asyncio
    async def test_record_incident(self):
        inc_id = await self.cm.record_incident("+79990000001", "test_error", "test detail", severity=2)
        assert inc_id > 0

    @pytest.mark.asyncio
    async def test_detect_no_crisis(self):
        result = await self.cm.detect_crisis("+79990000001", 1)
        assert result is None

    @pytest.mark.asyncio
    async def test_detect_crisis_high_reports(self):
        for _ in range(6):
            await self.cm.record_incident("+79990000002", "spam_report")
        result = await self.cm.detect_crisis("+79990000002", 6)
        assert result is not None
        assert result["status"] == "paused"

    def test_get_active_crises_empty(self):
        crises = self.cm.get_active_crises()
        assert isinstance(crises, list)

    @pytest.mark.asyncio
    async def test_get_active_crises_with_data(self):
        await self.cm.record_incident("+79990000001", "test", severity=3)
        crises = self.cm.get_active_crises()
        assert len(crises) >= 1

    @pytest.mark.asyncio
    async def test_resolve_incident(self):
        inc_id = await self.cm.record_incident("+79990000001", "test")
        self.cm.resolve_incident(inc_id, "resolved via test")
        crises = self.cm.get_active_crises()
        assert all(c["id"] != inc_id for c in crises)

    @pytest.mark.asyncio
    async def test_check_account_health_safe(self):
        result = await self.cm.check_account_health("+79990000001", error_count=0, success_count=10)
        assert result["status"] == "safe"
        assert result["risk"] < 30

    @pytest.mark.asyncio
    async def test_check_account_health_danger(self):
        result = await self.cm.check_account_health("+79990000002", error_count=10, success_count=0)
        assert result["status"] in ("danger", "critical")

    @pytest.mark.asyncio
    async def test_get_account_health(self):
        await self.cm.check_account_health("+79990000001")
        health = self.cm.get_account_health()
        assert isinstance(health, list)

    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self):
        self.cm.start_monitoring()
        assert self.cm._monitor_task is not None
        self.cm.stop_monitoring()
        assert self.cm._monitor_task is None


class TestAutomationEngine:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.path = self.tmp.name
        self.tmp.close()
        self.engine = AutomationEngine(db_path=self.path)

    def teardown_method(self):
        try:
            os.remove(self.path)
        except PermissionError:
            time.sleep(0.1)
            try:
                os.remove(self.path)
            except PermissionError:
                pass

    @pytest.mark.asyncio
    async def test_create_rule(self):
        rule_id = await self.engine.create_rule("Test Rule", "error",
            [{"field": "status", "operator": "eq", "value": "error"}],
            [{"type": "notify", "params": {"message": "Error detected!"}}])
        assert rule_id > 0

    def test_list_rules_empty(self):
        assert self.engine.list_rules() == []

    @pytest.mark.asyncio
    async def test_list_rules_with_data(self):
        await self.engine.create_rule("Test", "event", [], [])
        assert len(self.engine.list_rules()) == 1

    @pytest.mark.asyncio
    async def test_evaluate_rule_conditions_match(self):
        rule_id = await self.engine.create_rule("Conds", "test", [{"field": "x", "operator": "eq", "value": 1}], [])
        result = await self.engine.evaluate_rule(rule_id, "test", {"x": 1})
        assert result is not None

    @pytest.mark.asyncio
    async def test_evaluate_rule_conditions_no_match(self):
        rule_id = await self.engine.create_rule("NoMatch", "test", [{"field": "x", "operator": "eq", "value": 1}], [])
        result = await self.engine.evaluate_rule(rule_id, "test", {"x": 2})
        assert result is None

    @pytest.mark.asyncio
    async def test_trigger_webhook_bad_url(self):
        result = await self.engine.trigger_webhook("http://nonexistent.local/test", {"test": True}, retries=1, timeout=1)
        assert result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_emit_event(self):
        await self.engine.create_rule("EmitTest", "my_event", [],
            [{"type": "notify", "params": {"message": "hello"}}])
        await self.engine.emit("my_event", {"data": 1})
        triggers = self.engine.list_triggers()
        assert len(triggers) >= 1

    @pytest.mark.asyncio
    async def test_add_webhook_config(self):
        wid = await self.engine.add_webhook_config("test", "http://example.com/webhook")
        assert wid > 0

    @pytest.mark.asyncio
    async def test_list_webhooks(self):
        await self.engine.add_webhook_config("test", "http://example.com/webhook")
        hooks = self.engine.list_webhooks()
        assert len(hooks) >= 1

    def test_get_stats(self):
        stats = self.engine.get_stats()
        assert "total_rules" in stats
        assert "total_triggers" in stats

    @pytest.mark.asyncio
    async def test_on_handler(self):
        events = []
        self.engine.on("custom_event", lambda d: events.append(d))
        await self.engine.emit("custom_event", {"msg": "hello"})
        assert len(events) == 1
        assert events[0]["msg"] == "hello"


class TestAutoFunnel:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.path = self.tmp.name
        self.tmp.close()
        self.funnel = AutoFunnelEngine(db_path=self.path)

    def teardown_method(self):
        try:
            os.remove(self.path)
        except PermissionError:
            time.sleep(0.1)
            try:
                os.remove(self.path)
            except PermissionError:
                pass

    @pytest.mark.asyncio
    async def test_create_funnel(self):
        fid = await self.funnel.create_funnel("Test Campaign", "Get leads")
        assert fid > 0

    @pytest.mark.asyncio
    async def test_list_funnels(self):
        await self.funnel.create_funnel("Test", "Goal")
        funnels = self.funnel.list_funnels()
        assert len(funnels) == 1

    @pytest.mark.asyncio
    async def test_get_funnel_status(self):
        fid = await self.funnel.create_funnel("Test", "Goal")
        status = self.funnel.get_funnel_status(fid)
        assert status is not None
        assert status["name"] == "Test"
        assert status["status"] == "active"

    def test_get_nonexistent_funnel(self):
        assert self.funnel.get_funnel_status(999) is None

    @pytest.mark.asyncio
    async def test_stop_funnel(self):
        import asyncio
        fid = await self.funnel.create_funnel("Test", "Goal")
        async def dummy():
            await asyncio.sleep(3600)
        task = asyncio.create_task(dummy())
        self.funnel.active_funnels[fid] = task
        self.funnel.stop_funnel(fid)
        status = self.funnel.get_funnel_status(fid)
        assert status["status"] == "cancelled"
