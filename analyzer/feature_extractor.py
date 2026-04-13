from datetime import datetime, timezone


def extract_features(profile: dict) -> dict:
    if not profile:
        return {}

    features = {}

    # --- Account age ---
    try:
        created  = datetime.fromisoformat(
            profile["created_at"].replace("Z", "+00:00")
        )
        age_days = (datetime.now(timezone.utc) - created).days
    except Exception:
        age_days = 0

    features["account_age_days"] = age_days
    features["is_new_account"]   = age_days < 90

    # --- Follower/Following ratio ---
    followers = profile.get("followers_count", 0) or 0
    following = profile.get("following_count", 1) or 1
    features["follower_ratio"]    = round(followers / following, 3)
    features["follow_heavy"]      = following > (followers * 10) and followers < 500
    features["broadcast_pattern"] = followers > 500 and following < 50

    # --- Tweet velocity ---
    tweet_count = profile.get("tweet_count", 0) or 0
    features["tweets_per_day"]    = round(tweet_count / age_days, 2) if age_days > 0 else 0
    features["abnormal_velocity"] = features["tweets_per_day"] > 50

    # --- Likes given ---
    likes = profile.get("likes_given", 0) or 0
    features["likes_given"]         = likes
    features["like_tweet_ratio"]    = round(likes / tweet_count, 2) if tweet_count > 0 else 0
    features["abnormal_like_ratio"] = features["like_tweet_ratio"] > 100

    # --- Profile completeness ---
    has_image    = profile.get("has_profile_image", False)
    has_bio      = profile.get("has_bio", False)
    has_location = bool(profile.get("location", ""))
    has_name     = bool(profile.get("display_name", ""))

    features["has_profile_image"]    = has_image
    features["has_bio"]              = has_bio
    features["has_location"]         = has_location
    features["profile_completeness"] = sum([has_image, has_bio, has_location, has_name])

    # --- Utility bot signals ---
    bio_lower        = profile.get("bio", "").lower()
    utility_keywords = [
        "bot", "automated", "auto", "alerts", "updates",
        "feed", "tracker", "monitor", "official", "service"
    ]
    features["self_identifies_as_bot"] = any(k in bio_lower for k in utility_keywords)
    features["stated_purpose"]         = next(
        (k for k in utility_keywords if k in bio_lower), None
    )

    # --- Content signals ---
    tweets = profile.get("recent_tweets", [])
    if tweets:
        features["avg_tweet_length"]     = round(sum(len(t) for t in tweets) / len(tweets), 1)
        unique_ratio                     = len(set(tweets)) / len(tweets)
        features["content_unique_ratio"] = round(unique_ratio, 2)
        features["highly_repetitive"]    = unique_ratio < 0.5
        url_count                        = sum(1 for t in tweets if "http" in t)
        features["url_heavy"]            = url_count > (len(tweets) * 0.6)

        scam_keywords = [
            "giveaway", "crypto", "dm me", "limited time", "free",
            "click here", "earn", "investment", "winner", "claim"
        ]
        features["keyword_flags"] = [
            k for k in scam_keywords
            if any(k in t.lower() for t in tweets)
        ]

        influence_keywords = [
            "maga", "deep state", "fake news", "mainstream media",
            "they don't want you", "wake up", "censored"
        ]
        features["influence_flags"] = [
            k for k in influence_keywords
            if any(k in t.lower() for t in tweets)
        ]
    else:
        features["avg_tweet_length"]     = 0
        features["content_unique_ratio"] = 1.0
        features["highly_repetitive"]    = False
        features["url_heavy"]            = False
        features["keyword_flags"]        = []
        features["influence_flags"]      = []

    # --- Tweet client signals ---
    clients = profile.get("tweet_clients", [])
    features["uses_suspicious_client"] = any(
        c and "Twitter" not in c and "X " not in c for c in clients
    )
    features["tweet_clients"] = clients

    return features
