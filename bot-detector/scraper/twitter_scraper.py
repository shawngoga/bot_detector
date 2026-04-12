import asyncio
import os
from twikit import Client
from datetime import datetime, timezone

class TwitterScraper:
    def __init__(self):
        self.client = Client('en-US')
        self.cookie_file = "cookies.json"

    async def login(self):
        """Login once, save cookies, reuse to avoid repeated logins."""
        if os.path.exists(self.cookie_file):
            self.client.load_cookies(self.cookie_file)
            print("[*] Loaded existing session.")
        else:
            await self.client.login(
                auth_info_1=os.getenv("TWITTER_USERNAME"),
                auth_info_2=os.getenv("TWITTER_EMAIL"),
                password=os.getenv("TWITTER_PASSWORD")
            )
            self.client.save_cookies(self.cookie_file)
            print("[*] Logged in and saved session.")

    async def get_mentions(self):
        """Fetch latest mentions of the bot account."""
        try:
            notifications = await self.client.get_mentions()
            return notifications
        except Exception as e:
            print(f"[-] Error fetching mentions: {e}")
            return []

    async def get_user_profile(self, username: str) -> dict:
        """Fetch all signal data for a target username."""
        await asyncio.sleep(3)  # Human-like delay

        try:
            user = await self.client.get_user_by_screen_name(username)
        except Exception as e:
            print(f"[-] Could not fetch user @{username}: {e}")
            return {}

        await asyncio.sleep(2)

        # Fetch recent tweets
        try:
            tweets = await self.client.get_user_tweets(
                user.id, 'Tweets', count=20
            )
        except Exception:
            tweets = []

        tweet_texts  = [t.text for t in tweets] if tweets else []
        tweet_times  = [str(t.created_at) for t in tweets] if tweets else []
        tweet_clients = list(set([
            t.source for t in tweets if hasattr(t, 'source') and t.source
        ])) if tweets else []

        # Fetch following list (for network mapping)
        await asyncio.sleep(2)
        try:
            following = await self.client.get_user_following(user.id, count=100)
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
            "has_profile_image":  not user.profile_image_url_https.endswith(
                                      'default_profile_normal.png'),
            "has_bio":            bool(user.description),
            "bio":                user.description or "",
            "location":           user.location or "",
            "recent_tweets":      tweet_texts[:10],
            "recent_tweet_times": tweet_times[:10],
            "tweet_clients":      tweet_clients,
            "following_list":     following_names,
        }