"""
GRAMGPT — Channel Discovery & Promotion Script
1. Search Telegram for channels relevant to our niche (Telegram bots, marketing, crypto)
2. Filter by open comments
3. Analyze @teleboost_ai
4. Generate promotional comments
"""
import asyncio, os, sys, json, logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["TELEGRAM_API_ID"] = "23658639"
os.environ["TELEGRAM_API_HASH"] = "cfb36ccc9fda771f58107ab86642098c"
os.environ["TELEGRAM_PHONE"] = "+79158443612"

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

TELEGRAM_API_ID = 23658639
TELEGRAM_API_HASH = "cfb36ccc9fda771f58107ab86642098c"

OUR_CHANNEL = "teleboost_ai"
SESSION_PATH = "data/sessions/gramgpt_user.session"

# Keywords for searching relevant channels
TOPIC_KEYWORDS = [
    "telegram bot",
    "telegram marketing",
    "crypto signals",
    "ai telegram",
    "telegram growth",
    "crypto trading",
    "deFi",
    "airdrop",
    "crypto news",
    "trading signals",
    "telegram automation",
    "blockchain",
]

from telethon import TelegramClient
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.types import Channel
from telethon.errors import FloodWaitError


async def main():
    client = TelegramClient(SESSION_PATH, TELEGRAM_API_ID, TELEGRAM_API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        print("❌ Not authorized. Session invalid.")
        return

    me = await client.get_me()
    print(f"✅ Authorized as {me.first_name} @{me.username} (id={me.id})")
    print()

    # ─── STEP 1: Search channels by keywords ───────────────────────────
    print("=" * 60)
    print("STEP 1: Searching channels by topic keywords")
    print("=" * 60)

    all_channels = {}
    for kw in TOPIC_KEYWORDS:
        try:
            result = await client(SearchRequest(q=kw, limit=30))
            for chat in result.chats:
                if isinstance(chat, Channel) and getattr(chat, "username", None):
                    u = chat.username
                    if u not in all_channels:
                        all_channels[u] = {
                            "username": u,
                            "title": getattr(chat, "title", "Unknown"),
                            "members": getattr(chat, "participants_count", 0),
                            "keyword": kw,
                        }
            print(f"  '{kw}' → {len(result.chats)} chats, {len(all_channels)} unique so far")
        except FloodWaitError as e:
            print(f"  ⏳ Flood wait {e.seconds}s for '{kw}', skipping...")
        except Exception as e:
            print(f"  ⚠️  Error '{kw}': {e}")
        await asyncio.sleep(1.5)

    # Sort by members descending
    sorted_channels = sorted(all_channels.values(), key=lambda c: c["members"], reverse=True)
    print(f"\n📊 Total unique channels found: {len(sorted_channels)}")
    print(f"   Top 20 by members:")
    for i, ch in enumerate(sorted_channels[:20], 1):
        print(f"   {i:2d}. @{ch['username']:30s} {ch['members']:>8,} members  (kw: {ch['keyword']})")

    # ─── STEP 2: Filter by open comments ───────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 2: Checking which channels have open comments")
    print("=" * 60)

    channels_with_comments = []
    for ch in sorted_channels[:50]:  # Check top 50
        try:
            entity = await client.get_entity(ch["username"])
            if isinstance(entity, Channel):
                has_link = bool(getattr(entity, "has_link", False))
                is_restricted = bool(getattr(entity, "restricted", False) or getattr(entity, "forbidden", False))
                if has_link and not is_restricted:
                    channels_with_comments.append(ch)
                    print(f"  ✅ @{ch['username']:30s} {ch['members']:>8,} members — OPEN COMMENTS")
                else:
                    print(f"  ❌ @{ch['username']:30s} — {'restricted' if is_restricted else 'no discussion group'}")
        except Exception as e:
            print(f"  ⚠️  @{ch['username']}: {type(e).__name__}")
        await asyncio.sleep(1)

    print(f"\n📊 Channels with open comments: {len(channels_with_comments)}")

    # Save results
    os.makedirs("data", exist_ok=True)
    with open("data/discovered_channels.json", "w", encoding="utf-8") as f:
        json.dump({
            "all_found": len(sorted_channels),
            "with_comments": len(channels_with_comments),
            "channels": channels_with_comments[:100],
        }, f, ensure_ascii=False, indent=2)
    print(f"💾 Saved to data/discovered_channels.json")

    # Show top 15 with comments
    print(f"\n🏆 TOP 15 channels with open comments:")
    for i, ch in enumerate(channels_with_comments[:15], 1):
        print(f"   {i:2d}. @{ch['username']:30s} {ch['members']:>8,} members")

    # ─── STEP 3: Analyze our channel @teleboost_ai ─────────────────────
    print("\n" + "=" * 60)
    print(f"STEP 3: Analyzing @{OUR_CHANNEL}")
    print("=" * 60)

    try:
        entity = await client.get_entity(OUR_CHANNEL)
        print(f"   Title: {getattr(entity, 'title', '?')}")
        print(f"   Members: {getattr(entity, 'participants_count', 0)}")
        print(f"   Has discussion: {getattr(entity, 'has_link', False)}")

        messages = []
        async for msg in client.iter_messages(entity, limit=5):
            messages.append({
                "id": msg.id,
                "text": (msg.text or "")[:200],
                "date": str(msg.date)[:19] if msg.date else "?",
                "views": getattr(msg, "views", 0),
            })

        print(f"\n   Last 5 posts:")
        for i, m in enumerate(messages, 1):
            print(f"   {i}. [{m['date']}] views={m['views']} | {m['text'][:100]}")

        os.makedirs("data", exist_ok=True)
        with open("data/teleboost_ai_info.json", "w", encoding="utf-8") as f:
            json.dump({"channel": OUR_CHANNEL, "messages": messages}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"   ⚠️  Could not fetch @{OUR_CHANNEL}: {e}")

    # ─── STEP 4: Generate promo text via AI ─────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 4: Generating promo text for @teleboost_ai")
    print("=" * 60)

    try:
        from src.core.ai_client import ai_client
        prompt = (
            f"I have a Telegram channel @{OUR_CHANNEL} about AI-powered Telegram marketing and automation.\n"
            f"Generate 3 different short promotional comments (max 150 chars each) in Russian that:\n"
            f"- Look natural, NOT spammy\n"
            f"- Can be posted as comments under crypto/marketing Telegram posts\n"
            f"- Mention @{OUR_CHANNEL} naturally\n"
            f"- Offer value (tips, insights) not just promotion\n"
            f"Format: return ONLY a JSON list of 3 strings, no other text."
        )
        response = await ai_client.get_chat_response(0, [{"role": "user", "content": prompt}])
        print(f"   AI Response: {response[:300]}...")

        # Try to parse JSON from response
        import re
        json_match = re.search(r'\[.*?\]', response, re.DOTALL)
        if json_match:
            promos = json.loads(json_match.group())
            print(f"\n   Generated promos:")
            for i, p in enumerate(promos, 1):
                print(f"   {i}. {p[:120]}")
            with open("data/promo_texts.json", "w", encoding="utf-8") as f:
                json.dump(promos, f, ensure_ascii=False, indent=2)
        else:
            print(f"   Could not parse JSON from response, saving raw")
            with open("data/promo_texts.json", "w", encoding="utf-8") as f:
                f.write(response)
    except Exception as e:
        print(f"   ⚠️  AI promo generation failed: {e}")
        print("   Using fallback promo texts")
        promos = [
            f"Отличный разбор! Кстати, у нас в @{OUR_CHANNEL} тоже делимся подобными инсайтами по Telegram-маркетингу и AI-автоматизации. Заходите!",
            f"Полезная информация! Если интересна тема автоматизации Telegram с помощью ИИ, рекомендую канал @{OUR_CHANNEL} — там много практических кейсов.",
            f"Согласен с автором. Кстати, кто хочет глубже разобраться в продвижении Telegram-каналов — загляните на @{OUR_CHANNEL}, делимся реальными стратегиями.",
        ]
        with open("data/promo_texts.json", "w", encoding="utf-8") as f:
            json.dump(promos, f, ensure_ascii=False, indent=2)

    # ─── SUMMARY ────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"   Channels found:      {len(sorted_channels)}")
    print(f"   With open comments:  {len(channels_with_comments)}")
    print(f"   Our channel:         @{OUR_CHANNEL}")
    print(f"\n   Next step: Use promo texts to comment in top channels")
    print(f"   Promo texts saved to: data/promo_texts.json")
    print(f"   Target channels:     data/discovered_channels.json")
    
    await client.disconnect()
    print("\n✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())
