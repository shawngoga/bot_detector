import asyncio
import base64
import json
import os
import tempfile
from twikit import Client
from datetime import datetime, timezone


class TwitterScraper:
    def __init__(self):
        self.client = Client('en-US')
        self.cookie_file = "cookies.json"

    async def login(self):
    cookies_b64 = os.getenv("TWITTER_COOKIES")
    print(f"[*] TWITTER_COOKIES present: {bool(cookies_b64)}")
    if cookies_b64:
        try:
            cookies_json = base64.b64decode(cookies_b64).decode('utf-8')
            cookies = json.loads(cookies_json)
            for key, value in cookies.items():
                self.client.http.cookies.set(key, value)
            print("[*] Loaded cookies from environment.")
            return
        except Exception as e:
            print(f"[-] Env cookie error: {e}")
    if os.path.exists(self.cookie_file):
        self.client.load_cookies(self.cookie_file)
        print("[*] Loaded cookies from file.")
    else:
        print("[-] No cookies found.")

    async def get_mentions(self):
        try:
            notifications = await self.client.get_notifications('Mentions')
            return notifications
        except Exception as e:
            print(f"[-] Error fetching mentions: {e}")
            return []

    async def get_user_profile(self, username: str) -> dict:
        await asyncio.sleep(3)
        try:
            user = await self.client.get_user_by_screen_name(username)
        except Exception as e:
            print(f"[-] Could not fetch @{username}: {e}")
            return {}

        await asyncio.sleep(2)

        try:
            tweets = await user.get_tweets('Tweets', count=20)
        except Exception:
            tweets = []

        tweet_texts   = [t.text for t in tweets] if tweets else []
        tweet_times   = [str(t.created_at) for t in tweets] if tweets else []
        tweet_clients = list(set([
            t.source for t in tweets
            if hasattr(t, 'source') and t.source
        ])) if tweets else []

        await asyncio.sleep(2)
        try:
            following       = await user.get_following(count=100)
            following_names = [u.screen_name for u in following]
        except Exception:
            following_names = []

        return {
            "username":           username,
            "user_id":            user.id,
            "display_name":       user.name,
            "created_at":         str(user.created_at),
            "followers_count":    user.followers_count,
            "following_count":    user.following_count,
            "tweet_count":        user.statuses_count,
            "likes_given":        user.favourites_count,
            "verified":           user.verified,
            "has_profile_image":  not user.profile_image_url.endswith(
                                      'default_profile_normal.png'),
            "has_bio":            bool(user.description),
            "bio":                user.description or "",
            "location":           user.location or "",
            "recent_tweets":      tweet_texts[:10],
            "recent_tweet_times": tweet_times[:10],
            "tweet_clients":      tweet_clients,
            "following_list":     following_names,
        }
