"""
Promo Engine - AI-generated promotional comments with anti-spam protection.
Generates unique promo text and validates against spam filters.
"""

import logging
import random
import re
from typing import List, Dict, Optional, Any

from src.core.ai_client import ai_client

logger = logging.getLogger(__name__)


class PromoEngine:
    """
    Generates promotional comments with AI variations and spam protection.
    """
    
    # Base promo templates with placeholders
    PROMO_TEMPLATES = [
        "{hook} {value} {cta} {link}",
        "{hook} {cta} {value} {link}",
        "{value} {hook} {link} {cta}",
        "{cta} {value} {link} {hook}",
    ]
    
    # Hook variations (attention grabbers)
    HOOKS = [
        "Отличная точка зрения! 👏",
        "Кстати, по этой теме... 🤔",
        "Интересно, что вы упомянули это 💡",
        "Как раз об этом думал 😊",
        "Классный пост! 🔥",
        "Хороший анализ 💪",
        "На самом деле, есть ещё один нюанс...",
        "Это напомнило мне...",
        "Согласен с основной мыслью 👍",
        "Интересное наблюдение 🤔",
    ]
    
    # Value propositions
    VALUES = [
        "я недавно нашёл способ автоматизировать подобные задачи и экономить 10+ часов в неделю",
        "мы собрали базу проверенных инструментов для этого направления",
        "есть чек-лист из 15 пунктов, который помогает не упустить важное",
        "создали простой гайд, который разбирает это по шагам",
        "провели исследование и выявили 7 ключевых факторов успеха",
        "есть кейс, где удалось достичь результата за 2 недели",
        "собрали лучшие практики в одном месте",
        "нашли способ упростить этот процесс в 3 раза",
    ]
    
    # Call-to-actions
    CTAS = [
        "Может быть полезно:",
        "Если интересно — смотрите здесь:",
        "Вдруг пригодится:",
        "Делюсь на всякий случай:",
        "Кому актуально — заходите:",
        "Оставлю здесь:",
        "Нашёл для себя полезным:",
        "Рекомендую глянуть:",
    ]
    
    # Spam keywords to avoid
    SPAM_PATTERNS = [
        r'\b[Bb][Uu][Yy]\s+[Nn][Oo][Ww]\b',
        r'\b[Cc][Ll][Ii][Cc][Kk]\s+[Hh][Ee][Rr][Ee]\b',
        r'\b[Ff][Rr][Ee][Ee]\s*[Mm][Oo][Nn][Ee][Yy]\b',
        r'\b[Ll][Ii][Mm][Ii][Tt][Ee][Dd]\s*[Tt][Ii][Mm][Ee]\b',
        r'\b[Aa][Cc][Tt]\s*[Nn][Oo][Ww]\b',
        r'\b[Aa][Mm][Aa][Zz][Ii][Nn][Gg]\s*[Oo][Ff][Ff][Ee][Rr]\b',
        r'\$\d+[Kk]?\s*[Pp][Ee][Rr]\s*[Dd][Aa][Yy]',
        r'\b[Ee][Aa][Rr][Nn]\s*\$\d+',
        r'\b[Ww][Oo][Rr][Kk]\s*[Ff][Rr][Oo][Mm]\s*[Hh][Oo][Mm][Ee]\b',
        r'\b[Pp][Aa][Ss][Ss][Ii][Vv][Ee]\s*[Ii][Nn][Cc][Oo][Mm][Ee]\b',
    ]
    
    # Max caps percentage
    MAX_CAPS_RATIO = 0.3
    
    # Max link density (links per 100 chars)
    MAX_LINK_DENSITY = 0.05
    
    def __init__(self, settings: Optional[Dict] = None):
        """
        Initialize PromoEngine.
        
        Args:
            settings: Configuration dict
        """
        self.settings = settings or {}
        self.generated_history: List[str] = []  # Track to avoid exact repeats
        
        logger.info("🎯 PromoEngine initialized")
    
    async def generate_promo_comment(
        self,
        post_text: str = "",
        target_link: str = "",
        mode: str = "balanced",
        use_ai: bool = True
    ) -> str:
        """
        Generate promotional comment with anti-spam protection.
        
        Args:
            post_text: Original post text (for context)
            target_link: Link to insert
            mode: 'safe', 'balanced', 'aggressive' (spam risk tolerance)
            use_ai: If True, use AI to generate unique variations
        
        Returns:
            Ready-to-post promo comment or fallback template
        """
        max_attempts = 5
        
        for attempt in range(max_attempts):
            # Generate candidate
            if use_ai and ai_client.is_available:
                candidate = await self._generate_with_ai(post_text, target_link)
            else:
                candidate = self._generate_from_template(target_link)
            
            # Validate
            spam_score = self._calculate_spam_score(candidate, mode)
            
            if spam_score < self._get_max_spam_score(mode):
                logger.info(f"✅ Generated promo (score: {spam_score:.2f}, attempt: {attempt+1})")
                self.generated_history.append(candidate)
                # Keep history limited
                if len(self.generated_history) > 100:
                    self.generated_history.pop(0)
                return candidate
            else:
                logger.debug(f"⚠️ Spam score too high ({spam_score:.2f}), retrying...")
        
        # Fallback to safest template
        logger.warning("⚠️ All AI attempts failed spam check, using fallback")
        return self._generate_fallback(target_link)
    
    async def _generate_with_ai(self, post_text: str, target_link: str) -> str:
        """Generate promo using AI with context awareness."""
        prompt = f"""
You are writing a natural, helpful comment reply to a Telegram post.

Post context (first 200 chars): {post_text[:200]}

Your task:
1. Write 1-2 sentences that relate to the post topic naturally
2. Mention you have a relevant resource/link that might help
3. Keep it conversational, not salesy
4. Use casual Russian (if post is Russian) or English
5. Do NOT use ALL CAPS, multiple exclamation marks, or spam phrases
6. End with the link naturally incorporated

Example good comments:
- "Кстати, недавно решал похожую задачу через автоматизацию. Может пригодится: {target_link}"
- "Интересный взгляд. У нас получилось упростить этот процесс, делюсь: {target_link}"

Write your comment (max 150 chars):
"""
        
        try:
            response = await ai_client.generate(
                prompt,
                max_tokens=100,
                temperature=0.7
            )
            
            if response and target_link not in response:
                response += f" {target_link}"
            
            return response or self._generate_from_template(target_link)
            
        except Exception as e:
            logger.error(f"AI generation error: {e}")
            return self._generate_from_template(target_link)
    
    def _generate_from_template(self, target_link: str) -> str:
        """Generate from template with random variations."""
        # Pick random components
        template = random.choice(self.PROMO_TEMPLATES)
        hook = random.choice(self.HOOKS)
        value = random.choice(self.VALUES)
        cta = random.choice(self.CTAS)
        
        # Mask link for variety
        link = self._mask_link(target_link)
        
        # Fill template
        comment = template.format(
            hook=hook,
            value=value,
            cta=cta,
            link=link
        )
        
        return comment
    
    def _generate_fallback(self, target_link: str) -> str:
        """Safest fallback when all else fails."""
        return f"Интересный пост 👍 У нас есть полезные материалы по этой теме: {target_link}"
    
    def _mask_link(self, link: str) -> str:
        """Mask link to look less spammy."""
        masks = [
            link,
            f"t.me/{link.split('/')[-1]}",
            f"@{link.split('/')[-1].replace('@', '')}",
        ]
        return random.choice(masks)
    
    def _calculate_spam_score(self, text: str, mode: str) -> float:
        """
        Calculate spam likelihood score (0-1, lower is better).
        
        Factors:
        - Caps ratio
        - Exclamation density
        - Link density
        - Spam keyword matches
        - Repetition from history
        """
        score = 0.0
        
        # 1. Caps ratio (0-0.3 weight)
        if text:
            caps_count = sum(1 for c in text if c.isupper())
            caps_ratio = caps_count / len(text)
            score += min(caps_ratio / self.MAX_CAPS_RATIO * 0.3, 0.3)
        
        # 2. Exclamation density (0-0.2 weight)
        excl_count = text.count('!')
        if len(text) > 0:
            excl_density = excl_count / len(text)
            score += min(excl_density * 10, 0.2)
        
        # 3. Link density (0-0.2 weight)
        link_count = len(re.findall(r'https?://|t\.me/|@\w+', text))
        if len(text) > 0:
            link_density = link_count * 20 / len(text)  # normalized
            score += min(link_density / self.MAX_LINK_DENSITY * 0.2, 0.2)
        
        # 4. Spam keywords (0-0.2 weight per match, max 0.4)
        spam_matches = 0
        for pattern in self.SPAM_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                spam_matches += 1
        score += min(spam_matches * 0.2, 0.4)
        
        # 5. Repetition check (0-0.1 weight)
        if text in self.generated_history[-20:]:  # Check last 20
            score += 0.1
        
        return min(score, 1.0)
    
    def _get_max_spam_score(self, mode: str) -> float:
        """Get maximum acceptable spam score for mode."""
        thresholds = {
            "safe": 0.15,
            "balanced": 0.3,
            "aggressive": 0.5
        }
        return thresholds.get(mode, 0.3)
    
    def validate_comment(self, text: str, mode: str = "balanced") -> Dict[str, Any]:
        """
        Validate existing comment against spam filters.
        
        Returns:
            Validation result with score and warnings
        """
        score = self._calculate_spam_score(text, mode)
        max_score = self._get_max_spam_score(mode)
        
        warnings = []
        
        if score > max_score:
            warnings.append(f"Spam score {score:.2f} exceeds threshold {max_score}")
        
        # Check specific issues
        caps_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
        if caps_ratio > self.MAX_CAPS_RATIO:
            warnings.append(f"Too many caps ({caps_ratio*100:.0f}%)")
        
        if text.count('!') > 2:
            warnings.append("Too many exclamation marks")
        
        link_count = len(re.findall(r'https?://|t\.me/|@\w+', text))
        if link_count > 2:
            warnings.append(f"Too many links ({link_count})")
        
        return {
            "valid": score <= max_score and len(warnings) == 0,
            "spam_score": round(score, 2),
            "threshold": max_score,
            "warnings": warnings
        }
