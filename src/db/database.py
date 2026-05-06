import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "gramgpt.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            # Accounts & Sessions
            conn.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone TEXT UNIQUE,
                    device_type TEXT,
                    fingerprint TEXT,
                    proxy TEXT,
                    status TEXT DEFAULT 'idle',
                    risk_score INTEGER DEFAULT 0,
                    dna_profile TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Campaigns
            conn.execute("""
                CREATE TABLE IF NOT EXISTS campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    goal TEXT,
                    strategy_json TEXT,
                    roi_predicted TEXT,
                    status TEXT DEFAULT 'planned',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Leads
            conn.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tg_id INTEGER UNIQUE,
                    username TEXT,
                    engagement_score INTEGER DEFAULT 0,
                    ltv_estimate REAL DEFAULT 0,
                    status TEXT DEFAULT 'new',
                    last_contact DATETIME
                )
            """)
            # NEW: Billing & Subscriptions
            conn.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    chat_id INTEGER PRIMARY KEY,
                    plan_type TEXT DEFAULT 'free',
                    actions_remaining INTEGER DEFAULT 100,
                    expires_at DATETIME
                )
            """)
            # NEW: Referrals
            conn.execute("""
                CREATE TABLE IF NOT EXISTS referrals (
                    user_id INTEGER,
                    referred_by INTEGER,
                    status TEXT DEFAULT 'pending',
                    bonus_applied BOOLEAN DEFAULT 0,
                    PRIMARY KEY (user_id)
                )
            """)
            # Analytics
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER,
                    event_type TEXT,
                    cost REAL DEFAULT 0,
                    revenue REAL DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Legacy messages
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    role TEXT,
                    content TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # User settings (model choice)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    chat_id INTEGER PRIMARY KEY,
                    model_name TEXT DEFAULT 'gpt-4o'
                )
            """)
            # NEW: Account Pool for multi-account rotation
            conn.execute("""
                CREATE TABLE IF NOT EXISTS account_pool (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone TEXT UNIQUE,
                    session_path TEXT,
                    proxy TEXT,
                    status TEXT DEFAULT 'warming',
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_used DATETIME,
                    cooldown_until DATETIME,
                    success_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    last_error TEXT
                )
            """)
            # NEW: Proxy pool with validation stats
            conn.execute("""
                CREATE TABLE IF NOT EXISTS proxy_pool (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proxy_url TEXT UNIQUE,
                    proxy_type TEXT,
                    is_working BOOLEAN DEFAULT 1,
                    last_checked DATETIME,
                    response_time_ms REAL,
                    country TEXT,
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    error_count INTEGER DEFAULT 0
                )
            """)
            # NEW: Comment history for RAG and few-shot learning
            conn.execute("""
                CREATE TABLE IF NOT EXISTS comment_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_phone TEXT,
                    channel_username TEXT,
                    post_id INTEGER,
                    comment_text TEXT,
                    comment_type TEXT,
                    spam_score REAL,
                    was_edited BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    engagement_reactions INTEGER DEFAULT 0
                )
            """)
            # NEW: Sniper edit queue persistence
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sniper_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel TEXT,
                    post_id INTEGER,
                    emoji_msg_id INTEGER,
                    target_link TEXT,
                    post_text TEXT,
                    edit_after_seconds INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending'
                )
            """)
            conn.commit()

    def create_campaign(self, name: str, goal: str, strategy: Dict[str, Any]):
        roi = strategy.get("predicted_roi", "N/A")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO campaigns (name, goal, strategy_json, roi_predicted) VALUES (?, ?, ?, ?)",
                (name, goal, json.dumps(strategy), str(roi))
            )
            conn.commit()

    def get_roi_report(self, campaign_id: int) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT SUM(cost), SUM(revenue) FROM analytics WHERE campaign_id = ?", (campaign_id,))
            cost, revenue = cursor.fetchone()
            cost, revenue = cost or 1, revenue or 0
            return {"roi_actual": f"{(revenue/cost)*100:.1f}%", "total_revenue": revenue, "total_cost": cost}

    # Subscription Management
    def get_subscription(self, chat_id: int) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT plan_type, actions_remaining FROM subscriptions WHERE chat_id = ?", (chat_id,))
            row = cursor.fetchone()
            if row:
                return {"plan": row[0], "actions": row[1]}
            return {"plan": "free", "actions": 100}

    # Referral Management
    def add_referral(self, user_id: int, referrer_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR IGNORE INTO referrals (user_id, referred_by) VALUES (?, ?)", (user_id, referrer_id))
            conn.commit()

    # Legacy Bot methods
    def add_message(self, chat_id: int, role: str, content: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)", (chat_id, role, content))
            conn.commit()

    def get_history(self, chat_id: int, limit: int = 20) -> List[Dict[str, str]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id DESC LIMIT ?", (chat_id, limit))
            rows = cursor.fetchall()
            return [{"role": r, "content": c} for r, c in reversed(rows)]

    def clear_history(self, chat_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
            conn.commit()

    def get_user_model(self, chat_id: int) -> str:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT model_name FROM user_settings WHERE chat_id = ?", (chat_id,))
            row = cursor.fetchone()
            return row[0] if row else "gpt-4o"

    def set_user_model(self, chat_id: int, model_name: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO user_settings (chat_id, model_name) VALUES (?, ?)", (chat_id, model_name))
            conn.commit()

    # Account Pool Management (SQLite integration)
    def add_account_to_pool(self, phone: str, session_path: str, proxy: Optional[str] = None) -> bool:
        """Add account to SQLite pool."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO account_pool (phone, session_path, proxy, status) VALUES (?, ?, ?, ?)",
                    (phone, session_path, proxy, 'warming')
                )
                conn.commit()
            logger.info(f"✅ Added {phone} to account pool (DB)")
            return True
        except Exception as e:
            logger.error(f"❌ Error adding account to pool: {e}")
            return False
    
    def get_accounts_from_pool(self, status: Optional[str] = None) -> List[Dict]:
        """Load accounts from SQLite pool."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if status:
                    cursor = conn.execute(
                        "SELECT phone, session_path, proxy, status, last_used, cooldown_until, success_count, error_count, last_error FROM account_pool WHERE status = ?",
                        (status,)
                    )
                else:
                    cursor = conn.execute(
                        "SELECT phone, session_path, proxy, status, last_used, cooldown_until, success_count, error_count, last_error FROM account_pool"
                    )
                rows = cursor.fetchall()
                return [
                    {
                        'phone': r[0],
                        'session_path': r[1],
                        'proxy': r[2],
                        'status': r[3],
                        'last_used': r[4],
                        'cooldown_until': r[5],
                        'success_count': r[6],
                        'error_count': r[7],
                        'last_error': r[8]
                    }
                    for r in rows
                ]
        except Exception as e:
            logger.error(f"❌ Error loading accounts from pool: {e}")
            return []
    
    def update_account_status(self, phone: str, status: str, cooldown_minutes: int = 0) -> bool:
        """Update account status in SQLite."""
        try:
            cooldown_until = None
            if cooldown_minutes > 0:
                from datetime import timedelta
                cooldown_until = datetime.now() + timedelta(minutes=cooldown_minutes)
            
            with sqlite3.connect(self.db_path) as conn:
                if cooldown_until:
                    conn.execute(
                        "UPDATE account_pool SET status = ?, cooldown_until = ?, last_used = CURRENT_TIMESTAMP WHERE phone = ?",
                        (status, cooldown_until.isoformat(), phone)
                    )
                else:
                    conn.execute(
                        "UPDATE account_pool SET status = ?, last_used = CURRENT_TIMESTAMP WHERE phone = ?",
                        (status, phone)
                    )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Error updating account status: {e}")
            return False
    
    def record_account_action(self, phone: str, success: bool, error_message: Optional[str] = None) -> bool:
        """Record success/error for account."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if success:
                    conn.execute(
                        "UPDATE account_pool SET success_count = success_count + 1, last_error = NULL WHERE phone = ?",
                        (phone,)
                    )
                else:
                    conn.execute(
                        "UPDATE account_pool SET error_count = error_count + 1, last_error = ? WHERE phone = ?",
                        (error_message, phone)
                    )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Error recording account action: {e}")
            return False
    
    # Proxy Pool Management
    def add_proxy_to_pool(self, proxy_url: str, proxy_type: str) -> bool:
        """Add proxy to SQLite pool."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO proxy_pool (proxy_url, proxy_type, is_working) VALUES (?, ?, 1)",
                    (proxy_url, proxy_type)
                )
                conn.commit()
            logger.info(f"✅ Added proxy {proxy_url} to pool (DB)")
            return True
        except Exception as e:
            logger.error(f"❌ Error adding proxy to pool: {e}")
            return False
    
    def get_working_proxies(self) -> List[str]:
        """Get list of working proxies from DB."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT proxy_url FROM proxy_pool WHERE is_working = 1 ORDER BY response_time_ms ASC"
                )
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"❌ Error loading proxies: {e}")
            return []
    
    def update_proxy_status(self, proxy_url: str, is_working: bool, response_time_ms: Optional[float] = None) -> bool:
        """Update proxy validation status."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if response_time_ms is not None:
                    conn.execute(
                        "UPDATE proxy_pool SET is_working = ?, response_time_ms = ?, last_checked = CURRENT_TIMESTAMP WHERE proxy_url = ?",
                        (1 if is_working else 0, response_time_ms, proxy_url)
                    )
                else:
                    conn.execute(
                        "UPDATE proxy_pool SET is_working = ?, last_checked = CURRENT_TIMESTAMP WHERE proxy_url = ?",
                        (1 if is_working else 0, proxy_url)
                    )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Error updating proxy status: {e}")
            return False
    
    # Comment History (for RAG & Few-shot)
    def save_comment_to_history(
        self,
        account_phone: str,
        channel_username: str,
        post_id: int,
        comment_text: str,
        comment_type: str = "direct",
        spam_score: float = 0.0,
        was_edited: bool = False
    ) -> bool:
        """Save comment to history for RAG/few-shot learning."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO comment_history (account_phone, channel_username, post_id, comment_text, comment_type, spam_score, was_edited) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (account_phone, channel_username, post_id, comment_text, comment_type, spam_score, 1 if was_edited else 0)
                )
                conn.commit()
            logger.debug(f"📝 Saved comment to history: {channel_username}:{post_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving comment history: {e}")
            return False
    
    def get_recent_comments(self, limit: int = 50, comment_type: Optional[str] = None) -> List[Dict]:
        """Get recent comments for few-shot learning."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if comment_type:
                    cursor = conn.execute(
                        "SELECT channel_username, post_id, comment_text, comment_type, created_at FROM comment_history WHERE comment_type = ? ORDER BY created_at DESC LIMIT ?",
                        (comment_type, limit)
                    )
                else:
                    cursor = conn.execute(
                        "SELECT channel_username, post_id, comment_text, comment_type, created_at FROM comment_history ORDER BY created_at DESC LIMIT ?",
                        (limit,)
                    )
                rows = cursor.fetchall()
                return [
                    {
                        'channel': r[0],
                        'post_id': r[1],
                        'text': r[2],
                        'type': r[3],
                        'created_at': r[4]
                    }
                    for r in rows
                ]
        except Exception as e:
            logger.error(f"❌ Error loading comment history: {e}")
            return []
    
    # Sniper Queue Persistence
    def save_sniper_queue_item(self, channel: str, post_id: int, emoji_msg_id: int, target_link: str, post_text: str, edit_after_seconds: int) -> bool:
        """Save sniper edit queue item to DB (for crash recovery)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO sniper_queue (channel, post_id, emoji_msg_id, target_link, post_text, edit_after_seconds, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (channel, post_id, emoji_msg_id, target_link, post_text, edit_after_seconds, 'pending')
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Error saving sniper queue item: {e}")
            return False
    
    def get_pending_sniper_edits(self) -> List[Dict]:
        """Get pending sniper edits from DB."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT id, channel, post_id, emoji_msg_id, target_link, post_text, edit_after_seconds, created_at FROM sniper_queue WHERE status = 'pending'"
                )
                rows = cursor.fetchall()
                return [
                    {
                        'id': r[0],
                        'channel': r[1],
                        'post_id': r[2],
                        'emoji_msg_id': r[3],
                        'target_link': r[4],
                        'post_text': r[5],
                        'edit_after_seconds': r[6],
                        'created_at': r[7]
                    }
                    for r in rows
                ]
        except Exception as e:
            logger.error(f"❌ Error loading sniper queue: {e}")
            return []
    
    def mark_sniper_edit_completed(self, queue_id: int) -> bool:
        """Mark sniper edit as completed."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE sniper_queue SET status = 'completed' WHERE id = ?",
                    (queue_id,)
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Error updating sniper edit status: {e}")
            return False

db = Database()
