"""
Analytics & Account Admin Handlers - Multi-account management and reporting.
Commands: /add_account, /list_accounts, /export_stats, /risk_report
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
    
    Usage: /add_account <phone> <session_file> [proxy_url]
    Example: /add_account +79158443612 data/sessions/account2.session http://proxy:8080
    """
    if not is_admin(message.from_user.id):
        await message.answer("❌ Access denied")
        return
    
    args = message.text.split()[1:]
    
    if len(args) < 2:
        await message.answer(
            "❌ <b>Usage:</b> /add_account &lt;phone&gt; &lt;session_file&gt; [proxy]\n\n"
            "<b>Example:</b>\n"
            "/add_account +79158443612 data/sessions/account2.session\n"
            "/add_account +79158443612 data/sessions/account2.session socks5://proxy:1080",
            parse_mode="HTML"
        )
        return
    
    phone = args[0]
    session_file = args[1]
    proxy = args[2] if len(args) > 2 else None
    
    # Check if session file exists
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
            proxy=proxy,
            validate_proxy=True
        )
        
        if success:
            proxy_info = f"\n🔌 Proxy: <code>{proxy}</code>" if proxy else "\n🔌 No proxy (direct)"
            await message.answer(
                f"✅ <b>Account added successfully!</b>\n\n"
                f"📱 Phone: <code>{phone}</code>\n"
                f"📁 Session: <code>{session_file}</code>"
                f"{proxy_info}",
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
