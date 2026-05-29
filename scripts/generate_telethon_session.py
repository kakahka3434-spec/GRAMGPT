"""
Generate Telethon session file for GRAMGPT.
Run this locally (not on Render) where Telegram is accessible.

Usage:
    python scripts/generate_telethon_session.py

The script will:
1. Connect to Telegram using your phone number
2. Send a verification code via Telegram
3. Save the session to data/sessions/gramgpt_user.session
4. Test the connection to verify it works
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telethon import TelegramClient


async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID", "23658639"))
    api_hash = os.getenv("TELEGRAM_API_HASH", "cfb36ccc9fda771f58107ab86642098c")
    phone = os.getenv("TELEGRAM_PHONE", "+79158443612")

    os.makedirs("data/sessions", exist_ok=True)
    session_path = "data/sessions/gramgpt_user"

    client = TelegramClient(session_path, api_id, api_hash)

    print(f"Connecting to Telegram as {phone}...")
    await client.connect()

    if not await client.is_user_authorized():
        print("Sending verification code...")
        await client.send_code_request(phone)
        code = input(f"Enter the verification code sent to {phone}: ")
        await client.sign_in(phone, code)
        print("Authorized successfully!")
    else:
        print("Already authorized (existing session)")

    me = await client.get_me()
    print(f"\nConnected as: {me.first_name} {me.last_name} (@{me.username})")
    print(f"Session saved to: {session_path}.session")
    print(f"\nFile size: {os.path.getsize(session_path + '.session')} bytes")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
