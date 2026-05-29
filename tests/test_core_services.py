"""Unit tests for core services: AccountPool, RateLimiter, WorkModeController."""

import os
import tempfile
import pytest
from src.core.account_pool import AccountPool, AccountStatus
from src.core.rate_limiter import AdaptiveRateLimiter
from src.core.work_modes import WorkModeController


class TestAccountPool:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.path = self.tmp.name
        self.tmp.close()
        self.pool = AccountPool(pool_file=self.path)

    def teardown_method(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_add_and_list(self):
        ok = self.pool.add_account("+79990000001", "sessions/test.session")
        assert ok is True
        assert len(self.pool.list_accounts()) == 1

    def test_duplicate_rejected(self):
        self.pool.add_account("+79990000001", "sessions/test.session")
        ok = self.pool.add_account("+79990000001", "sessions/test.session")
        assert ok is False

    def test_remove_account(self):
        self.pool.add_account("+79990000001", "sessions/test.session")
        assert self.pool.remove_account("+79990000001") is True
        assert len(self.pool.list_accounts()) == 0

    def test_remove_nonexistent(self):
        assert self.pool.remove_account("+99999999999") is False

    def test_mark_status(self):
        self.pool.add_account("+79990000001", "sessions/test.session")
        ok = self.pool.mark_status("+79990000001", AccountStatus.COOLDOWN, cooldown_minutes=60)
        assert ok is True
        accs = self.pool.list_accounts()
        assert accs[0]["status"] == "cooldown"

    def test_get_next_active_round_robin(self):
        self.pool.add_account("+79990000001", "sessions/test1.session")
        self.pool.add_account("+79990000002", "sessions/test2.session")
        a1 = self.pool.get_next_active()
        a2 = self.pool.get_next_active()
        assert a1 is not None
        assert a2 is not None
        assert a1.phone != a2.phone

    def test_empty_pool_returns_none(self):
        assert self.pool.get_next_active() is None

    def test_record_success_error(self):
        self.pool.add_account("+79990000001", "sessions/test.session")
        self.pool.record_success("+79990000001")
        self.pool.record_success("+79990000001")
        self.pool.record_error("+79990000001", "test error")
        accs = self.pool.list_accounts()
        assert accs[0]["success_count"] == 2
        assert accs[0]["error_count"] == 1

    def test_health_report(self):
        self.pool.add_account("+79990000001", "sessions/test1.session")
        self.pool.add_account("+79990000002", "sessions/test2.session")
        self.pool.mark_status("+79990000001", AccountStatus.ACTIVE)
        report = self.pool.get_health_report()
        assert report["total"] == 2

    def test_get_formatted_report(self):
        self.pool.add_account("+79990000001", "sessions/test.session")
        fmt = self.pool.get_formatted_report()
        assert isinstance(fmt, str)
        assert len(fmt) > 0

    def test_update_proxy(self):
        self.pool.add_account("+79990000001", "sessions/test.session")
        ok = self.pool.update_account_proxy("+79990000001", proxy_id=None)
        assert ok is True

    def test_update_proxy_nonexistent(self):
        assert self.pool.update_account_proxy("+99999", proxy_id=None) is False

    def test_pool_persistence(self):
        self.pool.add_account("+79990000001", "sessions/test.session")
        pool2 = AccountPool(pool_file=self.path)
        assert len(pool2.list_accounts()) == 1

    def test_get_available_proxies(self):
        proxies = self.pool.get_available_proxies()
        assert isinstance(proxies, list)


class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_get_initial_delay(self):
        limiter = AdaptiveRateLimiter()
        delay = await limiter.get_delay("comment")
        assert delay >= 30 and delay <= 600

    @pytest.mark.asyncio
    async def test_error_streak_increases_delay(self):
        limiter = AdaptiveRateLimiter()
        delay_normal = await limiter.get_delay("comment")
        limiter.record_flood_wait(30)
        limiter.record_flood_wait(60)
        limiter.record_flood_wait(120)
        delay_after = await limiter.get_delay("comment")
        assert delay_after > delay_normal

    @pytest.mark.asyncio
    async def test_flood_wait_record(self):
        limiter = AdaptiveRateLimiter()
        limiter.record_flood_wait(60)
        assert limiter.last_flood_wait == 60

    @pytest.mark.asyncio
    async def test_different_action_delays(self):
        limiter = AdaptiveRateLimiter()
        d_comment = await limiter.get_delay("comment")
        d_reaction = await limiter.get_delay("reaction")
        d_scroll = await limiter.get_delay("scroll")
        assert d_comment != d_reaction or d_comment != d_scroll

    @pytest.mark.asyncio
    async def test_post_action_delay_returns_float(self):
        limiter = AdaptiveRateLimiter()
        import asyncio
        delay = await limiter.get_delay("reaction")
        assert delay > 0

    @pytest.mark.asyncio
    async def test_get_status(self):
        limiter = AdaptiveRateLimiter()
        status = limiter.get_status()
        assert "actions_per_hour" in status
        assert "error_streak" in status

    @pytest.mark.asyncio
    async def test_force_conservative_mode(self):
        limiter = AdaptiveRateLimiter()
        limiter.force_conservative_mode(60)
        assert limiter.error_streak >= 2

    @pytest.mark.asyncio
    async def test_conservative_mode_increases_delay(self):
        limiter = AdaptiveRateLimiter()
        normal = await limiter.get_delay("comment")
        limiter.force_conservative_mode(60)
        conservative = await limiter.get_delay("comment")
        assert conservative >= normal


class TestWorkModeController:
    def setup_method(self):
        self.controller = WorkModeController()

    def test_default_mode(self):
        assert self.controller.get_status()["current_mode"] == "balanced"

    def test_switch_mode(self):
        self.controller.switch_mode("aggressive", reason="manual")
        assert self.controller.get_status()["current_mode"] == "aggressive"

    def test_invalid_mode(self):
        assert self.controller.switch_mode("invalid_mode", reason="manual") is False

    def test_switch_to_same_mode(self):
        assert self.controller.switch_mode("balanced", reason="manual") is True

    def test_apply_to_rate_limiter(self):
        limiter = AdaptiveRateLimiter()
        self.controller.switch_mode("aggressive", reason="manual")
        self.controller.apply_to_rate_limiter(limiter)
        assert limiter.BASE_DELAYS["comment"][0] == 30

    def test_auto_downgrade(self):
        self.controller.switch_mode("aggressive", reason="manual")
        self.controller.current_mode = "aggressive"
        self.controller._manual_override = False
        self.controller.auto_downgrade(0.9)
        assert self.controller.get_status()["current_mode"] == "balanced"

    def test_no_downgrade_during_manual_override(self):
        self.controller.switch_mode("aggressive", reason="manual")
        self.controller.auto_downgrade(0.9)
        assert self.controller.get_status()["current_mode"] == "aggressive"

    def test_no_downgrade_low_risk(self):
        self.controller._manual_override = False
        self.controller.current_mode = "aggressive"
        self.controller.config = self.controller._get_config("aggressive")
        self.controller.auto_downgrade(0.1)
        assert self.controller.get_status()["current_mode"] == "aggressive"

    def test_no_downgrade_at_reliable(self):
        self.controller._manual_override = False
        self.controller.current_mode = "reliable"
        self.controller.config = self.controller._get_config("reliable")
        self.controller.auto_downgrade(0.9)
        assert self.controller.get_status()["current_mode"] == "reliable"

    def test_status_report(self):
        report = self.controller.get_status()
        assert "current_mode" in report
        assert "description" in report

    def test_formatted_status(self):
        formatted = self.controller.get_formatted_status()
        assert isinstance(formatted, str)
        assert len(formatted) > 20

    def test_reset_manual_override(self):
        self.controller.switch_mode("aggressive", reason="manual")
        assert self.controller._manual_override is True
        self.controller.reset_manual_override()
        assert self.controller._manual_override is False

    def test_get_pipeline_settings(self):
        settings = self.controller.get_pipeline_settings()
        assert "mode" in settings
        assert "max_comments_per_hour" in settings
