"""API integration tests for proxy and accounts endpoints using FastAPI TestClient."""

import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_200(self):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_health_has_service_checks(self):
        resp = client.get("/api/v1/health")
        data = resp.json()
        assert "services" in data
        assert "redis" in data["services"]


class TestProxyEndpoints:
    def test_list_proxies_empty(self):
        resp = client.get("/api/v1/proxy/list")
        assert resp.status_code == 200
        data = resp.json()
        assert "proxies" in data
        assert "total" in data

    def test_add_proxy_invalid_url(self):
        resp = client.post("/api/v1/proxy/add", json={"url": ""})
        assert resp.status_code == 400

    def test_add_proxy_valid(self):
        resp = client.post("/api/v1/proxy/add", json={"url": "socks5://user:pass@1.2.3.4:1080"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "added"
        assert "id" in data

    def test_add_bulk(self):
        resp = client.post("/api/v1/proxy/add-bulk", json={
            "urls": "socks5://a:b@1.2.3.4:1080\nhttp://c:d@5.6.7.8:3128"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["added"] >= 1

    def test_add_bulk_with_comments(self):
        resp = client.post("/api/v1/proxy/add-bulk", json={
            "urls": "# comment line\nsocks5://a:b@1.2.3.4:1080"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["added"] >= 1

    def test_delete_nonexistent_proxy(self):
        resp = client.delete("/api/v1/proxy/99999")
        assert resp.status_code == 404

    def test_stats_endpoint(self):
        resp = client.get("/api/v1/proxy/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "active" in data
        assert "avg_ping" in data


class TestAccountsEndpoints:
    def test_list_accounts(self):
        resp = client.get("/api/v1/accounts")
        assert resp.status_code == 200
        data = resp.json()
        assert "accounts" in data
        assert "total" in data

    def test_add_account(self):
        resp = client.post("/api/v1/accounts/add", json={
            "phone": "+79991112233",
            "session_path": "data/sessions/test.session",
        })
        if resp.status_code == 400:
            # Already exists from previous test run — delete and retry
            client.delete("/api/v1/accounts/%2B79991112233")
            resp = client.post("/api/v1/accounts/add", json={
                "phone": "+79991112233",
                "session_path": "data/sessions/test.session",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "added"

    def test_add_duplicate_account(self):
        resp = client.post("/api/v1/accounts/add", json={"phone": "+79991118899", "session_path": "data/sessions/test.session"})
        if resp.status_code == 400:
            client.delete("/api/v1/accounts/%2B79991118899")
            client.post("/api/v1/accounts/add", json={"phone": "+79991118899", "session_path": "data/sessions/test.session"})
        resp = client.post("/api/v1/accounts/add", json={"phone": "+79991118899", "session_path": "data/sessions/test.session"})
        assert resp.status_code == 400

    def test_get_account(self):
        client.post("/api/v1/accounts/add", json={"phone": "+79991114455", "session_path": "data/sessions/test.session"})
        resp = client.get("/api/v1/accounts/%2B79991114455")
        assert resp.status_code == 200
        data = resp.json()
        assert data["phone"] == "+79991114455"

    def test_get_nonexistent_account(self):
        resp = client.get("/api/v1/accounts/%2B99999999999")
        assert resp.status_code == 404

    def test_delete_account(self):
        client.post("/api/v1/accounts/add", json={"phone": "+79991116677", "session_path": "data/sessions/test.session"})
        resp = client.delete("/api/v1/accounts/%2B79991116677")
        assert resp.status_code == 200

    def test_delete_nonexistent(self):
        resp = client.delete("/api/v1/accounts/%2B99999999999")
        assert resp.status_code == 404

    def test_update_proxy(self):
        client.post("/api/v1/accounts/add", json={"phone": "+79991118899", "session_path": "data/sessions/test.session"})
        resp = client.patch("/api/v1/accounts/%2B79991118899/proxy", json={"proxy_id": None})
        assert resp.status_code == 200

    def test_available_proxies(self):
        resp = client.get("/api/v1/accounts/available-proxies")
        assert resp.status_code == 200
        data = resp.json()
        assert "proxies" in data


class TestCommentingEndpoints:
    def test_commenting_logs(self):
        resp = client.get("/api/v1/commenting/logs")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_reactions_stats(self):
        resp = client.get("/api/v1/reactions/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data

    def test_warmup_accounts(self):
        resp = client.get("/api/v1/warmup/accounts")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_dialogs_active(self):
        resp = client.get("/api/v1/dialogs/active")
        assert resp.status_code == 200
        data = resp.json()
        assert "dialogs" in data or "total_active" in data


class TestParsingEndpoints:
    def test_parsing_start_no_creds(self):
        resp = client.post("/api/v1/parsing/start", json={
            "parser_type": "keywords",
            "target": "test",
            "keywords": "",
            "limit": 100,
        })
        assert resp.status_code in (200, 503)


class TestAnalyticsEndpoints:
    def test_analytics_summary(self):
        resp = client.get("/api/v1/analytics/summary")
        assert resp.status_code == 200

    def test_dashboard(self):
        resp = client.get("/api/v1/dashboard")
        assert resp.status_code == 200

    def test_notifications(self):
        resp = client.get("/api/v1/notifications")
        assert resp.status_code in (200, 500)

    def test_audit_events(self):
        resp = client.get("/api/v1/audit/events")
        assert resp.status_code == 200
