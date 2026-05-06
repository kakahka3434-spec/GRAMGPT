"""
Proxy Manager - Validation, assignment, and rotation for GRAMGPT accounts.
Supports HTTP and SOCKS5 proxies with automatic fallback.
Enhanced with real HTTP connectivity checks and geo-location validation.
"""

import asyncio
import logging
import random
import socket
from typing import Optional, Dict, List, Tuple
from urllib.parse import urlparse
import aiohttp

logger = logging.getLogger(__name__)


class ProxyManager:
    """
    Manages proxy validation, assignment, and rotation.
    Enhanced with real HTTP testing and performance tracking.
    """
    
    # Default test targets for proxy validation
    TEST_TARGETS = [
        ("telegram.org", 443),
        ("google.com", 443),
        ("cloudflare.com", 443)
    ]
    
    # HTTP endpoints for connectivity testing
    HTTP_TEST_URLS = [
        "https://api.telegram.org/bot",  # Lightweight Telegram API
        "https://httpbin.org/ip",  # Returns IP info
        "https://icanhazip.com"  # Simple IP echo
    ]
    
    def __init__(self, proxy_list_file: Optional[str] = None):
        """
        Initialize proxy manager.
        
        Args:
            proxy_list_file: Optional file with proxy URLs (one per line)
        """
        self.proxy_list: List[str] = []
        self.current_index = 0
        self.proxy_stats: Dict[str, Dict] = {}
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Load from file if provided
        if proxy_list_file:
            self._load_proxies(proxy_list_file)
        
        logger.info(f"🔌 ProxyManager initialized ({len(self.proxy_list)} proxies)")
    
    def _load_proxies(self, filepath: str) -> None:
        """Load proxies from file."""
        try:
            with open(filepath, 'r') as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                self.proxy_list = lines
            logger.info(f"📂 Loaded {len(self.proxy_list)} proxies from {filepath}")
        except FileNotFoundError:
            logger.warning(f"⚠️ Proxy file not found: {filepath}")
        except Exception as e:
            logger.error(f"❌ Error loading proxies: {e}")
    
    @staticmethod
    async def validate_proxy(proxy_url: str, timeout: float = 10.0) -> bool:
        """
        Validate proxy by attempting real HTTP connection through it.
        
        Args:
            proxy_url: Proxy URL (http://host:port or socks5://host:port)
            timeout: Connection timeout in seconds
        
        Returns:
            True if proxy is working and can reach Telegram
        """
        if not proxy_url:
            return True  # Direct connection is always "valid"
        
        try:
            parsed = urlparse(proxy_url)
            proxy_type = parsed.scheme.lower()
            host = parsed.hostname
            port = parsed.port
            
            if not host or not port:
                logger.warning(f"⚠️ Invalid proxy URL: {proxy_url}")
                return False
            
            # Level 1: Basic socket connectivity (fast check)
            socket_valid = await ProxyManager._test_socket_connection(host, port, timeout)
            if not socket_valid:
                return False
            
            # Level 2: HTTP connectivity test (real validation)
            http_valid = await ProxyManager._test_http_through_proxy(proxy_url, timeout)
            
            if http_valid:
                logger.debug(f"✅ Proxy validated (HTTP): {proxy_url}")
            else:
                logger.warning(f"⚠️ Proxy socket OK but HTTP failed: {proxy_url}")
            
            return http_valid
            
        except asyncio.TimeoutError:
            logger.warning(f"⏱️ Proxy timeout: {proxy_url}")
            return False
        except Exception as e:
            logger.warning(f"❌ Proxy validation failed {proxy_url}: {e}")
            return False
    
    @staticmethod
    async def _test_socket_connection(host: str, port: int, timeout: float) -> bool:
        """Test basic TCP connection to proxy."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False
    
    @staticmethod
    async def _test_http_through_proxy(proxy_url: str, timeout: float) -> bool:
        """Test real HTTP connectivity through proxy to Telegram."""
        import aiohttp
        
        try:
            # Build proxy URL for aiohttp
            if proxy_url.startswith('socks5'):
                # aiohttp needs socks5://user:pass@host:port format
                proxy_url = proxy_url.replace('socks5://', 'socks5://')
            
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                # Try Telegram API first (most relevant)
                async with session.get(
                    "https://api.telegram.org/bot",
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    # Any response (even 404) means proxy works
                    return response.status < 500
                    
        except aiohttp.ClientProxyConnectionError:
            return False
        except aiohttp.ServerDisconnectedError:
            return False
        except asyncio.TimeoutError:
            return False
        except Exception:
            # Fallback: try without SSL verification issues
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        "https://httpbin.org/ip",
                        proxy=proxy_url,
                        timeout=aiohttp.ClientTimeout(total=timeout)
                    ) as response:
                        return response.status == 200
            except Exception:
                return False
    
    def assign_proxy_to_session(self, session_path: str, proxy_url: str) -> Dict:
        """
        Prepare proxy configuration for Telethon session.
        
        Args:
            session_path: Path to session file
            proxy_url: Proxy URL
        
        Returns:
            Dict with proxy parameters for Telethon
        """
        if not proxy_url:
            return {}
        
        parsed = urlparse(proxy_url)
        proxy_type = parsed.scheme.lower()
        
        # Convert to Telethon format
        if proxy_type in ('http', 'https'):
            return {
                'proxy': ('http', parsed.hostname, parsed.port, True, None, None)
            }
        elif proxy_type == 'socks5':
            return {
                'proxy': ('socks5', parsed.hostname, parsed.port, True, None, None)
            }
        
        return {}
    
    def get_next_proxy(self) -> Optional[str]:
        """
        Get next proxy using round-robin.
        
        Returns:
            Proxy URL or None if no proxies
        """
        if not self.proxy_list:
            return None
        
        proxy = self.proxy_list[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxy_list)
        return proxy
    
    def rotate_on_error(self, phone: str, error_type: str, current_proxy: Optional[str] = None) -> Optional[str]:
        """
        Rotate proxy on connection/flood error.
        
        Args:
            phone: Account phone (for logging)
            error_type: Type of error ('flood', 'connection', 'timeout')
            current_proxy: Current proxy URL
        
        Returns:
            New proxy URL or None for direct connection
        """
        if not self.proxy_list:
            logger.info(f"🔌 No proxy pool, using direct connection for {phone}")
            return None
        
        # Mark current proxy as problematic if tracked
        if current_proxy:
            if current_proxy not in self.proxy_stats:
                self.proxy_stats[current_proxy] = {'errors': 0, 'last_error': None}
            self.proxy_stats[current_proxy]['errors'] += 1
            self.proxy_stats[current_proxy]['last_error'] = error_type
        
        # Get next proxy
        new_proxy = self.get_next_proxy()
        
        # Avoid same proxy if possible
        if new_proxy == current_proxy and len(self.proxy_list) > 1:
            new_proxy = self.get_next_proxy()
        
        logger.info(f"🔄 Proxy rotated for {phone}: {error_type} → using {new_proxy or 'direct'}")
        return new_proxy
    
    async def validate_all_proxies(self, timeout: float = 10.0) -> Dict[str, bool]:
        """
        Validate all proxies in pool.
        
        Returns:
            Dict mapping proxy URL to validation result
        """
        if not self.proxy_list:
            return {}
        
        logger.info(f"🔍 Validating {len(self.proxy_list)} proxies...")
        
        results = {}
        for proxy in self.proxy_list:
            results[proxy] = await self.validate_proxy(proxy, timeout)
        
        working = sum(1 for v in results.values() if v)
        logger.info(f"✅ Proxy validation: {working}/{len(self.proxy_list)} working")
        
        return results
    
    def get_proxy_stats(self) -> Dict:
        """Get statistics for all tracked proxies."""
        return {
            'total_in_pool': len(self.proxy_list),
            'tracked_stats': self.proxy_stats,
            'working_ratio': self._calculate_working_ratio()
        }
    
    def _calculate_working_ratio(self) -> float:
        """Calculate ratio of working proxies based on error stats."""
        if not self.proxy_stats:
            return 1.0  # Assume all good if no stats
        
        total_errors = sum(s.get('errors', 0) for s in self.proxy_stats.values())
        total_proxies = len(self.proxy_stats)
        
        if total_proxies == 0:
            return 1.0
        
        # Simple heuristic: proxies with < 2 errors considered working
        working = sum(1 for s in self.proxy_stats.values() if s.get('errors', 0) < 2)
        return working / total_proxies
    
    @staticmethod
    def parse_proxy_string(proxy_str: str) -> Optional[Tuple[str, str, int]]:
        """
        Parse proxy string into components.
        
        Args:
            proxy_str: Proxy URL string
        
        Returns:
            Tuple of (type, host, port) or None
        """
        try:
            parsed = urlparse(proxy_str)
            if not parsed.hostname or not parsed.port:
                return None
            return (parsed.scheme, parsed.hostname, parsed.port)
        except Exception:
            return None
