import asyncio
import json
import os
from twikit import Client
from datetime import datetime, timezone

HARDCODED_COOKIES = {"__gpi": "UID=000013c42b769fa3:T=1776049249:RT=1776049592:S=ALNI_MZY9PBAzc0qaaVBkf7rWrELCNxyCA", "auth_token": "f106acfeda916912516895ef12680300d22f0c5d", "guest_id": "v1%3A177604924292046320", "twid": "u%3D1872098217791229952", "__gads": "ID=eb7a978e055dca9b:T=1776049249:RT=1776049592:S=ALNI_MZ_1TuCrpC4hUdnE0XAH7edv1XDiw", "auth_multi": "\"2040982323173216256:afc72ed8059ea472036880e263b3dc76fc6aad95\"", "_twpid": "tw.1775443047933.305473417732723608", "__cf_bm": "A5XEo_SsCjHRuRMQJv5c0UkkbLpxA_Spz3DmQdEIee4-1776049410.858675-1.0.1.1-44egr2fTOK.zVKeAFWWK8M3EqvVeZWMZkZ0Dt8Yf8mzr9STCGg.TtBdu7.Y2XAjUamBgCdAKRb4jd5.NFMNvP4h308QUvwJ6VItQ3GwseA65sIBIOz7e7SANg7vIagqX", "ct0": "e7c1028cbd205277129559dd13de0411cf539ff4651fd929e180f0eb6374fa90b41c64e7cefc4c230a66431344d195780cd6ac4ea87788f4f4bfdd9e68a98e349c5ea2475c26a8288977f6903b3b983a", "dnt": "1", "guest_id_ads": "v1%3A177604924292046320", "guest_id_marketing": "v1%3A177604924292046320", "kdt": "RV3RD6cXzhM6D9YT0vpJJxSltzGYHnUG2OAREE9w", "personalization_id": "\"v1_8mEWUbcuq/Re+uIk5qPDDQ==\""}

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
            notifs = await self.client.get_notifications('Mentions')
            print(f"[*] Got {len(notifs)} mention notifications")
            return [n for n in notifs if n.tweet is not None]
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
