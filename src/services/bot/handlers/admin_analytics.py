"""
Analytics & Account Admin Handlers - Multi-account management and reporting.
Commands: /add_account, /remove_account, /list_accounts, /list_proxies, /export_stats, /risk_report, /analytics, /mark_cooldown
"""

import logging
import os
from typing import Optional

from aiogram import Router, types, F
from aiogram.filters import Command

from src.config import settings
from src.core.account_pool import AccountPool, AccountStatus
from src.services.analytics_exporter import AnalyticsExporter

logger = logging.getLogger(__name__)

# Router for analytics commands
router = Router()

# Global instances (initialized on first use)
_account_pool: Optional[AccountPool] = None
_analytics_exporter: Optional[AnalyticsExporter] = None

# Admin IDs
ADMIN_IDS = set()


def is_admin(user_id: int) -> bool:
    """Check if user is authorized."""
    return True  # Open for now


def get_account_pool() -> AccountPool:
    """Get or initialize account pool."""
    global _account_pool
    if _account_pool is None:
        _account_pool = AccountPool()
    return _account_pool


def get_analytics_exporter() -> AnalyticsExporter:
    """Get or initialize analytics exporter."""
    global _analytics_exporter
    if _analytics_exporter is None:
        _analytics_exporter = AnalyticsExporter(
            account_pool=get_account_pool()
        )
    return _analytics_exporter


@router.message(Command("add_account"))
async def cmd_add_account(message: types.Message):
    """
    Add new account to pool.
    
    Usage: /add_account <phone> <session_file> [proxy_id]
    Example: /add_account +79158443612 data/sessions/account2.session 1
    """
    if not is_admin(message.from_user.id):
        await message.answer("❌ Access denied")
        return
    
    args = message.text.split()[1:]
    
    if len(args) < 2:
        await message.answer(
            "❌ <b>Usage:</b> /add_account &lt;phone&gt; &lt;session_file&gt; [proxy_id]\n\n"
            "<b>Examples:</b>\n"
            "/add_account +79158443612 data/sessions/account2.session\n"
            "/add_account +79158443612 data/sessions/account2.session 1\n\n"
            "Use /list_proxies to see available proxy IDs.",
            parse_mode="HTML"
        )
        return
    
    phone = args[0]
    session_file = args[1]
    proxy_id = int(args[2]) if len(args) > 2 and args[2].isdigit() else None
    
    if not os.path.exists(session_file):
        await message.answer(
            f"❌ Session file not found: <code>{session_file}</code>\n"
            f"Create it first with Telethon auth.",
            parse_mode="HTML"
        )
        return
    
    await message.answer(f"⏳ Adding account {phone}...")
    
    try:
        pool = get_account_pool()
        success = pool.add_account(
            phone=phone,
            session_path=session_file,
            proxy_id=proxy_id,
        )
        
        if success:
            proxy_label = f"\n🆔 Proxy ID: <code>{proxy_id}</code>" if proxy_id else "\n🔌 No proxy (direct)"
            await message.answer(
                f"✅ <b>Account added successfully!</b>\n\n"
                f"📱 Phone: <code>{phone}</code>\n"
                f"📁 Session: <code>{session_file}</code>"
                f"{proxy_label}",
                parse_mode="HTML"
            )
        else:
            await message.answer(
                f"⚠️ Account <code>{phone}</code> already exists or failed validation.",
                parse_mode="HTML"
            )
            
    except Exception as e:
        logger.error(f"Add account error: {e}")
        await message.answer(f"❌ Error: {e}")


@router.message(Command("remove_account"))
async def cmd_remove_account(message: types.Message):
    """Remove account from pool by phone."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Access denied")
        return
    
    args = message.text.split()[1:]
    if not args:
        await message.answer("❌ Usage: /remove_account <phone>")
        return
    
    phone = args[0]
    
    try:
        pool = get_account_pool()
        success = pool.remove_account(phone)
        
        if success:
            await message.answer(f"✅ Account <code>{phone}</code> removed", parse_mode="HTML")
        else:
            await message.answer(f"⚠️ Account <code>{phone}</code> not found", parse_mode="HTML")
            
    except Exception as e:
        await message.answer(f"❌ Error: {e}")


@router.message(Command("list_accounts"))
async def cmd_list_accounts(message: types.Message):
    """List all accounts in pool with status."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Access denied")
        return
    
    try:
        pool = get_account_pool()
        report = pool.get_formatted_report()
        
        # Add detailed list
        accounts = pool.list_accounts()
        
        if not accounts:
            await message.answer("📭 <b>No accounts in pool</b>\n\nUse /add_account to add one.", parse_mode="HTML")
            return
        
        details = []
        for acc in accounts[:10]:  # Show first 10
            status_emoji = {
                "active": "🟢",
                "warming": "🟡",
                "cooldown": "⏰",
                "banned": "🔴",
                "error": "⚠️"
            }.get(acc['status'], "⚪")
            
            proxy_info = "🔌" if acc.get('proxy') else "📡"
            
            details.append(
                f"{status_emoji} <code>{acc['phone']}</code> | "
                f"{acc['status']} | "
                f"S:{acc.get('success_count', 0)} E:{acc.get('error_count', 0)} | "
                f"{proxy_info}"
            )
        
        full_report = f"{report}\n\n<b>Accounts:</b>\n" + "\n".join(details)
        
        if len(full_report) > 4000:
            # Send in parts
            await message.answer(report, parse_mode="HTML")
            await message.answer("<b>Accounts (truncated):</b>\n" + "\n".join(details[:5]), parse_mode="HTML")
        else:
            await message.answer(full_report, parse_mode="HTML")
            
    except Exception as e:
        logger.error(f"List accounts error: {e}")
        await message.answer(f"❌ Error: {e}")


@router.message(Command("export_stats"))
async def cmd_export_stats(message: types.Message):
    """
    Export analytics to CSV or JSON.
    
    Usage: /export_stats [hours] [format]
    Example: /export_stats 24 csv
    """
    if not is_admin(message.from_user.id):
        await message.answer("❌ Access denied")
        return
    
    args = message.text.split()[1:]
    hours = int(args[0]) if args and args[0].isdigit() else 24
    fmt = args[1].lower() if len(args) > 1 else "csv"
    
    await message.answer(f"⏳ Generating {fmt.upper()} export for last {hours}h...")
    
    try:
        exporter = get_analytics_exporter()
        
        if fmt == "json":
            filepath = await exporter.export_json(hours=hours)
        else:
            filepath = await exporter.export_csv(hours=hours)
        
        # Send file
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            await message.answer_document(
                types.FSInputFile(filepath),
                caption=f"✅ Analytics export ({hours}h)"
            )
        else:
            await message.answer("⚠️ Export failed or empty")
            
    except Exception as e:
        logger.error(f"Export error: {e}")
        await message.answer(f"❌ Error: {e}")


@router.message(Command("risk_report"))
async def cmd_risk_report(message: types.Message):
    """Generate comprehensive risk assessment report."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Access denied")
        return
    
    args = message.text.split()[1:]
    hours = int(args[0]) if args and args[0].isdigit() else 24
    
    await message.answer("⏳ Generating risk report...")
    
    try:
        exporter = get_analytics_exporter()
        report = await exporter.generate_risk_report()
        
        await message.answer(report, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Risk report error: {e}")
        await message.answer(f"❌ Error: {e}")


@router.message(Command("analytics"))
async def cmd_analytics(message: types.Message):
    """Quick analytics summary."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Access denied")
        return
    
    args = message.text.split()[1:]
    hours = int(args[0]) if args and args[0].isdigit() else 24
    
    try:
        exporter = get_analytics_exporter()
        summary = await exporter.generate_summary_text(hours)
        
        await message.answer(summary, parse_mode="HTML")
        
    except Exception as e:
        await message.answer(f"❌ Error: {e}")


@router.message(Command("mark_cooldown"))
async def cmd_mark_cooldown(message: types.Message):
    """
    Manually mark account as cooldown.
    
    Usage: /mark_cooldown <phone> <minutes>
    """
    if not is_admin(message.from_user.id):
        await message.answer("❌ Access denied")
        return
    
    args = message.text.split()[1:]
    if len(args) < 2:
        await message.answer("❌ Usage: /mark_cooldown <phone> <minutes>")
        return
    
    phone = args[0]
    minutes = int(args[1]) if args[1].isdigit() else 60
    
    try:
        pool = get_account_pool()
        success = pool.mark_status(
            phone=phone,
            status=AccountStatus.COOLDOWN,
            cooldown_minutes=minutes
        )
        
        if success:
            await message.answer(
                f"⏰ Account <code>{phone}</code> on cooldown for {minutes} minutes",
                parse_mode="HTML"
            )
        else:
            await message.answer(f"⚠️ Account <code>{phone}</code> not found", parse_mode="HTML")
            
    except Exception as e:
        await message.answer(f"❌ Error: {e}")


@router.message(Command("list_proxies"))
async def cmd_list_proxies(message: types.Message):
    """List available proxies from the pool."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Access denied")
        return

    try:
        import sqlite3
        conn = sqlite3.connect("gramgpt.db")
        rows = conn.execute(
            "SELECT id, type, host, port, is_active, ping_ms, country, url "
            "FROM proxies ORDER BY id"
        ).fetchall()
        conn.close()

        if not rows:
            await message.answer(
                "📭 <b>No proxies in pool</b>\n\n"
                "Add proxies via the Proxy Manager page or use /add_account without proxy.",
                parse_mode="HTML"
            )
            return

        lines = ["<b>📡 Proxy Pool:</b>\n"]
        for r in rows:
            status = "🟢" if r[4] else "🔴"
            ping = f"{r[5]}ms" if r[5] else "—"
            country = f" ({r[6]})" if r[6] else ""
            url_short = r[7] if r[7] else f"{r[1]}://{r[2]}:{r[3]}"
            lines.append(
                f"{status} <b>ID {r[0]}</b>: <code>{url_short}</code>"
                f"{country} | Ping: {ping}"
            )

        msg = "\n".join(lines)
        if len(msg) > 4000:
            msg = msg[:4000] + "\n\n... (truncated)"

        await message.answer(msg, parse_mode="HTML")

    except Exception as e:
        logger.error(f"List proxies error: {e}")
        await message.answer(f"❌ Error: {e}")
