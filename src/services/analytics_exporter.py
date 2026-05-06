"""
Analytics Exporter - Metrics calculation and CSV/JSON export for GRAMGPT.
Aggregates data from comment_memory, pipeline stats, and account pool.
"""

import csv
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from src.db.comment_memory import comment_memory
from src.core.account_pool import AccountPool, AccountStatus

logger = logging.getLogger(__name__)


class AnalyticsExporter:
    """
    Generates analytics reports and exports data in various formats.
    """
    
    def __init__(
        self,
        account_pool: Optional[AccountPool] = None,
        pipeline_stats: Optional[Dict] = None
    ):
        """
        Initialize analytics exporter.
        
        Args:
            account_pool: AccountPool instance for pool metrics
            pipeline_stats: Optional pipeline statistics dict
        """
        self.account_pool = account_pool
        self.pipeline_stats = pipeline_stats or {}
        
        # Ensure exports directory exists
        self.exports_dir = "exports"
        os.makedirs(self.exports_dir, exist_ok=True)
        
        logger.info("📊 AnalyticsExporter initialized")
    
    async def calculate_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Calculate comprehensive metrics for specified period.
        
        Args:
            hours: Time window for metrics (default 24h)
        
        Returns:
            Dict with all calculated metrics
        """
        now = datetime.now()
        cutoff = now - timedelta(hours=hours)
        
        # Get recent comments from memory
        all_recent = []
        if hasattr(comment_memory, 'get_all_recent'):
            all_recent = comment_memory.get_all_recent(hours=hours)
        
        # Calculate base metrics
        total_comments = len(all_recent)
        
        # Group by channel
        channel_stats = {}
        for comment in all_recent:
            channel = comment.get('channel', 'unknown')
            if channel not in channel_stats:
                channel_stats[channel] = {'count': 0, 'styles': []}
            channel_stats[channel]['count'] += 1
            if 'style' in comment:
                channel_stats[channel]['styles'].append(comment['style'])
        
        # Calculate success rate
        # Success = comments sent without error in pipeline
        success_count = total_comments  # Simplified: assume all recorded = success
        
        # Get errors from account pool
        pool_report = self.account_pool.get_health_report() if self.account_pool else {}
        total_errors = pool_report.get('total_errors', 0)
        
        total_actions = success_count + total_errors
        success_rate = (success_count / total_actions * 100) if total_actions > 0 else 100.0
        
        # Calculate comments per hour
        hours_actual = max(hours, 1)
        comments_per_hour = total_comments / hours_actual
        
        # Calculate average delays (from comment timestamps if available)
        avg_delay = self._calculate_avg_delay(all_recent)
        
        # Flood errors count (from last N hours in pool stats)
        flood_errors = pool_report.get('total_errors', 0)  # Simplified
        
        # Calculate risk score (0-100)
        risk_score = self._calculate_risk_score(pool_report, success_rate, flood_errors)
        
        # Get top channels
        top_channels = sorted(
            channel_stats.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:5]
        
        metrics = {
            "period_hours": hours,
            "generated_at": now.isoformat(),
            "total_comments": total_comments,
            "success_rate": round(success_rate, 1),
            "success_count": success_count,
            "error_count": total_errors,
            "comments_per_hour": round(comments_per_hour, 1),
            "avg_delay_seconds": round(avg_delay, 1) if avg_delay else None,
            "flood_errors": flood_errors,
            "risk_score": round(risk_score, 1),
            "risk_level": "high" if risk_score > 50 else "medium" if risk_score > 25 else "low",
            "active_accounts": pool_report.get('active', 0),
            "total_accounts": pool_report.get('total', 0),
            "accounts_on_cooldown": pool_report.get('cooldown', 0),
            "proxy_coverage": round(pool_report.get('proxy_coverage', 0), 1),
            "top_channels": [
                {"channel": ch, "comments": data['count'], "styles": list(set(data['styles']))}
                for ch, data in top_channels
            ]
        }
        
        logger.info(f"📊 Metrics calculated: {total_comments} comments, {success_rate}% success, risk: {risk_score}")
        
        return metrics
    
    def _calculate_avg_delay(self, comments: List[Dict]) -> Optional[float]:
        """Calculate average delay between comments."""
        if len(comments) < 2:
            return None
        
        try:
            timestamps = []
            for c in comments:
                ts = c.get('timestamp') or c.get('datetime')
                if ts:
                    if isinstance(ts, str):
                        timestamps.append(datetime.fromisoformat(ts.replace('Z', '+00:00')))
                    else:
                        timestamps.append(datetime.fromtimestamp(ts))
            
            if len(timestamps) < 2:
                return None
            
            timestamps.sort()
            delays = [(timestamps[i+1] - timestamps[i]).total_seconds() 
                     for i in range(len(timestamps)-1)]
            
            return sum(delays) / len(delays) if delays else None
        except Exception as e:
            logger.warning(f"Error calculating delays: {e}")
            return None
    
    def _calculate_risk_score(
        self,
        pool_report: Dict,
        success_rate: float,
        flood_errors: int
    ) -> float:
        """
        Calculate risk score (0-100).
        
        Factors:
        - Low success rate = higher risk
        - Many flood errors = higher risk
        - Accounts on cooldown = higher risk
        - Low active accounts = higher risk
        """
        score = 0.0
        
        total = pool_report.get('total', 1)
        
        # Cooldown accounts (0-30 points)
        cooldown_pct = pool_report.get('cooldown', 0) / total
        score += cooldown_pct * 30
        
        # Banned accounts (0-40 points)
        banned_pct = pool_report.get('banned', 0) / total
        score += banned_pct * 40
        
        # Success rate penalty (0-20 points)
        if success_rate < 80:
            score += (80 - success_rate) * 0.5
        
        # Flood errors (0-10 points, capped at 10)
        flood_score = min(flood_errors * 2, 10)
        score += flood_score
        
        return min(score, 100)  # Cap at 100
    
    async def export_csv(self, hours: int = 24, filename: Optional[str] = None) -> str:
        """
        Export comment data to CSV.
        
        Args:
            hours: Time window for export
            filename: Optional custom filename
        
        Returns:
            Path to exported file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gramgpt_export_{hours}h_{timestamp}.csv"
        
        filepath = os.path.join(self.exports_dir, filename)
        
        # Get data
        all_comments = []
        if hasattr(comment_memory, 'get_all_recent'):
            all_comments = comment_memory.get_all_recent(hours=hours)
        
        # Write CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'timestamp', 'channel', 'post_id', 'style', 
                'comment_preview', 'account_phone', 'status'
            ])
            
            # Data rows
            for comment in all_comments:
                writer.writerow([
                    comment.get('datetime', ''),
                    comment.get('channel', ''),
                    comment.get('post_id', ''),
                    comment.get('style', ''),
                    comment.get('comment_preview', '')[:50],
                    comment.get('account_phone', 'unknown'),
                    'success'
                ])
        
        logger.info(f"📁 CSV exported: {filepath} ({len(all_comments)} rows)")
        return filepath
    
    async def export_json(self, hours: int = 24, filename: Optional[str] = None) -> str:
        """
        Export full analytics report to JSON.
        
        Args:
            hours: Time window for export
            filename: Optional custom filename
        
        Returns:
            Path to exported file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gramgpt_analytics_{hours}h_{timestamp}.json"
        
        filepath = os.path.join(self.exports_dir, filename)
        
        # Get metrics
        metrics = await self.calculate_metrics(hours)
        
        # Add raw data if available
        all_comments = []
        if hasattr(comment_memory, 'get_all_recent'):
            all_comments = comment_memory.get_all_recent(hours=hours)
        
        report = {
            'metrics': metrics,
            'raw_data': {
                'comment_count': len(all_comments),
                'comments': all_comments[:100]  # Limit to first 100
            },
            'pool_status': self.account_pool.get_health_report() if self.account_pool else None,
            'export_info': {
                'generated_at': datetime.now().isoformat(),
                'period_hours': hours,
                'version': '1.0'
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📁 JSON exported: {filepath}")
        return filepath
    
    async def generate_risk_report(self) -> str:
        """
        Generate human-readable risk assessment report.
        
        Returns:
            Formatted report string
        """
        metrics = await self.calculate_metrics(hours=24)
        
        emoji = "🟢" if metrics['risk_level'] == 'low' else "🟡" if metrics['risk_level'] == 'medium' else "🔴"
        
        # Generate recommendations
        recommendations = []
        if metrics['risk_score'] > 50:
            recommendations.append("⚠️ HIGH RISK: Increase delays, reduce frequency immediately")
        if metrics['accounts_on_cooldown'] > 0:
            recommendations.append(f"⏰ {metrics['accounts_on_cooldown']} accounts on cooldown - wait for recovery")
        if metrics['success_rate'] < 70:
            recommendations.append("📉 Low success rate - check proxy quality and delays")
        if metrics['comments_per_hour'] > 15:
            recommendations.append("⚡ High frequency detected - risk of flood ban")
        if metrics['proxy_coverage'] < 50 and metrics['total_accounts'] > 1:
            recommendations.append("🔌 Low proxy coverage - add more proxies for safety")
        
        if not recommendations:
            recommendations.append("✅ All systems nominal - maintain current settings")
        
        report = f"""
{emoji} <b>Risk Report — Last 24h</b>

<b>Performance:</b>
• Comments: {metrics['total_comments']} ({metrics['comments_per_hour']}/hour)
• Success rate: {metrics['success_rate']}%
• Flood errors: {metrics['flood_errors']}

<b>Account Pool:</b>
• Active: {metrics['active_accounts']}/{metrics['total_accounts']}
• On cooldown: {metrics['accounts_on_cooldown']}
• Proxy coverage: {metrics['proxy_coverage']}%

<b>Risk Score:</b> {metrics['risk_score']}/100 ({metrics['risk_level'].upper()})

<b>Recommendations:</b>
{chr(10).join(recommendations)}

<b>Top Channels:</b>
{chr(10).join(f"• @{ch['channel']}: {ch['comments']} comments" for ch in metrics['top_channels'][:3]) if metrics['top_channels'] else '• No data'}
"""
        return report
    
    async def generate_summary_text(self, hours: int = 24) -> str:
        """Generate simple text summary for quick view."""
        metrics = await self.calculate_metrics(hours)
        
        return f"""
📊 <b>GRAMGPT Summary ({hours}h)</b>

Comments: {metrics['total_comments']} | Rate: {metrics['success_rate']}%
Accounts: {metrics['active_accounts']}/{metrics['total_accounts']} active
Risk: {metrics['risk_score']}/100 ({metrics['risk_level']})
"""
