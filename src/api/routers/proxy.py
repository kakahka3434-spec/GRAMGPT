from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import sqlite3, os, asyncio, time, re, random, socket
from urllib.parse import urlparse
from datetime import datetime

router = APIRouter(prefix="/api/v1/proxy", tags=["proxy"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "..", "..", "gramgpt.db")


def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS proxies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            type TEXT DEFAULT 'SOCKS5',
            host TEXT,
            port INTEGER,
            login TEXT,
            password TEXT,
            country TEXT,
            is_active INTEGER DEFAULT 1,
            ping_ms INTEGER,
            last_checked TEXT,
            error_count INTEGER DEFAULT 0,
            uptime REAL DEFAULT 100.0,
            accounts_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    return conn


class ProxyAdd(BaseModel):
    url: str


class ProxyBulkAdd(BaseModel):
    urls: str


def _parse_url(url: str) -> dict:
    url = url.strip()
    if not url:
        return None
    if "://" not in url:
        url = "socks5://" + url
    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.upper()
        host = parsed.hostname
        port = parsed.port
        login = parsed.username
        password = parsed.password
        if not host or not port:
            return None
        return {"url": url, "type": scheme, "host": host, "port": port, "login": login, "password": password}
    except Exception:
        return None


@router.get("/list")
async def list_proxies(page: int = 1, limit: int = 50):
    conn = _get_db()
    offset = (page - 1) * limit
    rows = conn.execute("SELECT * FROM proxies ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset)).fetchall()
    total = conn.execute("SELECT COUNT(*) as c FROM proxies").fetchone()["c"]
    active = conn.execute("SELECT COUNT(*) as c FROM proxies WHERE is_active=1").fetchone()["c"]
    uptime = _calc_uptime(conn)
    avg_ping = _calc_avg_ping(conn)
    conn.close()

    proxies = []
    for r in rows:
        proxies.append({
            "id": r["id"],
            "url": r["url"],
            "type": r["type"],
            "host": r["host"],
            "port": r["port"],
            "login": r["login"],
            "password": r["password"],
            "country": r["country"],
            "is_active": bool(r["is_active"]),
            "ping_ms": r["ping_ms"],
            "last_checked": r["last_checked"],
            "error_count": r["error_count"],
            "uptime": r["uptime"],
            "accounts_count": r["accounts_count"],
            "created_at": r["created_at"],
        })

    return {
        "total": total,
        "active": active,
        "uptime": uptime,
        "avg_ping": avg_ping,
        "proxies": proxies,
        "page": page,
        "pages": max(1, (total + limit - 1) // limit),
    }


def _calc_uptime(db) -> float:
    try:
        row = db.execute("SELECT AVG(uptime) as u FROM proxies WHERE is_active=1").fetchone()
        return round(row["u"], 1) if row["u"] else 100.0
    except Exception:
        return 100.0


def _calc_avg_ping(db) -> int:
    try:
        row = db.execute("SELECT AVG(ping_ms) as p FROM proxies WHERE is_active=1 AND ping_ms IS NOT NULL").fetchone()
        return round(row["p"]) if row["p"] else 0
    except Exception:
        return 0


@router.post("/add")
async def add_proxy(data: ProxyAdd):
    parsed = _parse_url(data.url)
    if not parsed:
        raise HTTPException(400, "Invalid proxy URL. Use format: type://host:port or host:port")

    conn = _get_db()
    cur = conn.execute(
        "INSERT INTO proxies (url, type, host, port, login, password) VALUES (?, ?, ?, ?, ?, ?)",
        (parsed["url"], parsed["type"], parsed["host"], parsed["port"], parsed["login"], parsed["password"]),
    )
    proxy_id = cur.lastrowid
    conn.commit()
    conn.close()
    return {"status": "added", "id": proxy_id, "proxy": parsed["url"]}


@router.post("/add-bulk")
async def add_proxy_bulk(data: ProxyBulkAdd):
    lines = [l.strip() for l in data.urls.split("\n") if l.strip() and not l.strip().startswith("#")]
    added = 0
    errors = []
    conn = _get_db()

    for line in lines:
        parsed = _parse_url(line)
        if not parsed:
            errors.append(line)
            continue
        conn.execute(
            "INSERT INTO proxies (url, type, host, port, login, password) VALUES (?, ?, ?, ?, ?, ?)",
            (parsed["url"], parsed["type"], parsed["host"], parsed["port"], parsed["login"], parsed["password"]),
        )
        added += 1

    conn.commit()
    conn.close()
    return {"status": "ok", "added": added, "errors": errors, "total_parsed": len(lines)}


@router.delete("/{proxy_id}")
async def delete_proxy(proxy_id: int):
    conn = _get_db()
    cur = conn.execute("DELETE FROM proxies WHERE id=?", (proxy_id,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(404, "Proxy not found")
    return {"status": "deleted", "id": proxy_id}


@router.post("/{proxy_id}/check")
async def check_proxy(proxy_id: int):
    conn = _get_db()
    row = conn.execute("SELECT * FROM proxies WHERE id=?", (proxy_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Proxy not found")

    url = row["url"]
    ping, ok = await _validate(url)

    conn.execute(
        "UPDATE proxies SET ping_ms=?, last_checked=datetime('now'), is_active=? WHERE id=?",
        (ping, 1 if ok else 0, proxy_id),
    )
    conn.commit()
    conn.close()

    return {"id": proxy_id, "is_active": ok, "ping_ms": ping}


@router.post("/check-all")
async def check_all_proxies():
    conn = _get_db()
    rows = conn.execute("SELECT * FROM proxies").fetchall()
    conn.close()

    results = []
    for row in rows:
        ping, ok = await _validate(row["url"])
        results.append({"id": row["id"], "is_active": ok, "ping_ms": ping})

    conn2 = _get_db()
    for r in results:
        conn2.execute(
            "UPDATE proxies SET ping_ms=?, last_checked=datetime('now'), is_active=? WHERE id=?",
            (r["ping_ms"], 1 if r["is_active"] else 0, r["id"]),
        )
    conn2.commit()
    conn2.close()

    active = sum(1 for r in results if r["is_active"])
    return {"status": "done", "total": len(results), "active": active, "results": results}


@router.get("/stats")
async def proxy_stats():
    conn = _get_db()
    total = conn.execute("SELECT COUNT(*) as c FROM proxies").fetchone()["c"]
    active = conn.execute("SELECT COUNT(*) as c FROM proxies WHERE is_active=1").fetchone()["c"]
    avg_ping = _calc_avg_ping(conn)
    uptime = _calc_uptime(conn)
    by_type = {}
    for r in conn.execute("SELECT type, COUNT(*) as c FROM proxies GROUP BY type").fetchall():
        by_type[r["type"]] = r["c"]
    conn.close()
    return {
        "total": total,
        "active": active,
        "inactive": total - active,
        "avg_ping": avg_ping,
        "uptime": uptime,
        "by_type": by_type,
    }


async def _validate(proxy_url: str, timeout: float = 8.0):
    if not proxy_url:
        return 0, False
    try:
        parsed = urlparse(proxy_url)
        host = parsed.hostname
        port = parsed.port
        if not host or not port:
            return 0, False

        start = time.monotonic()
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)

        scheme = parsed.scheme.lower()
        if scheme == "socks5":
            writer.write(bytes([0x05, 0x01, 0x00]))
            await writer.drain()
            resp = await asyncio.wait_for(reader.read(2), timeout=timeout)
            if len(resp) < 2 or resp[0] != 0x05:
                writer.close()
                return round((time.monotonic() - start) * 1000), False

        writer.close()
        elapsed = round((time.monotonic() - start) * 1000)
        return elapsed, True

    except (asyncio.TimeoutError, ConnectionRefusedError, OSError, Exception):
        return 0, False
