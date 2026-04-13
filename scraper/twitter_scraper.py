import asyncio
import json
import os
from twikit import Client
from datetime import datetime, timezone

HARDCODED_COOKIES = {"auth_token": "afc72ed8059ea472036880e263b3dc76fc6aad95", "guest_id": "v1%3A177602839572089002", "twid": "u%3D2040982323173216256", "_twpid": "tw.1775443047933.305473417732723608", "att": "1-1S1b5WxN0VjM2qsgvaneFDhNhZPR9MGmXFmkpQG1", "ct0": "810c8b74c57086aa0e66d531dd23afc38799d966c2835e75a83789c67068971152b65508434f5d72d2b0cae29da52dc94133d48d5b40a369bdbea19fc1b785b34aaa0fb2551138a0e47c0c84c2011a58", "guest_id_ads": "v1%3A177602839572089002", "guest_id_marketing": "v1%3A177602839572089002", "kdt": "RV3RD6cXzhM6D9YT0vpJJxSltzGYHnUG2OAREE9w", "personalization_id": "\"v1_8mEWUbcuq/Re+uIk5qPDDQ==\""}

BOT_USERNAME = "bot_Detector_UC"

class TwitterScraper:
    def __init__(self):
        self.client = Client('en-US')
        self.cookie_file = "cookies.json"

    async def login(self):
        for k, v in HARDCODED_COOKIES.items():
            self.client.http.cookies.set(k, v)
        print("[*] Loaded hardcoded cookies.")

    async def get_mentions(self):
        try:
            tweets = await self.client.get_latest_timeline()
            mentions = [
                t for t in tweets
                if f"@{BOT_USERNAME}".lower() in t.text.lower()
            ]
            print(f"[*] Found {len(mentions)} mentions in timeline")
            return mentions
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
        tweet_clients = list(set([t.source for t in tweets if hasattr(t, 'source') and t.source])) if tweets else []
        await asyncio.sleep(2)
        try:
            following = await user.get_following(count=100)
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
            "has_profile_image":  not user.profile_image_url.endswith('default_profile_normal.png'),
            "has_bio":            bool(user.description),
            "bio":                user.description or "",
            "location":           user.location or "",
            "recent_tweets":      tweet_texts[:10],
            "recent_tweet_times": tweet_times[:10],
            "tweet_clients":      tweet_clients,
            "following_list":     following_names,
        }
