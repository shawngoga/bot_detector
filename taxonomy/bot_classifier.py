def rule_based_prescore(profile: dict, features: dict) -> list:
    hints = []

    # --- Utility bot (check first to avoid false positives) ---
    if features.get("self_identifies_as_bot"):
        hints.append("UTILITY_BOT: Account explicitly identifies as automated in bio")
    if features.get("broadcast_pattern") and features.get("self_identifies_as_bot"):
        hints.append("UTILITY_BOT: Broadcast-only pattern consistent with legitimate service bot")

    # --- Engagement bot ---
    if features.get("abnormal_like_ratio"):
        hints.append("ENGAGEMENT_BOT: Abnormally high like-to-tweet ratio detected")
    if features.get("abnormal_reply_ratio"):
        hints.append("ENGAGEMENT_BOT: Abnormally high reply frequency — possible reply loop bot")
    if features.get("follow_heavy"):
        hints.append("ENGAGEMENT_BOT: Following far more accounts than followers")
    if features.get("is_new_account") and features.get("abnormal_velocity"):
        hints.append("ENGAGEMENT_BOT: New account with inhuman tweet velocity")

    # --- Influence bot ---
    if features.get("influence_flags"):
        hints.append(
            f"INFLUENCE_BOT: Narrative keywords detected: "
            f"{', '.join(features['influence_flags'])}"
        )
    if features.get("highly_repetitive") and features.get("tweets_per_day", 0) > 20:
        hints.append("INFLUENCE_BOT: High volume repetitive content — possible astroturfing")
    if features.get("follower_ratio", 0) > 50 and features.get("is_new_account"):
        hints.append("INFLUENCE_BOT: Suspiciously high follower ratio for account age")

    # --- Scam bot ---
    if features.get("keyword_flags"):
        hints.append(
            f"SCAM_BOT: Scam keywords detected: "
            f"{', '.join(features['keyword_flags'])}"
        )
    if features.get("url_heavy") and features.get("is_new_account"):
        hints.append("SCAM_BOT: New account posting high volume of external links")
    if features.get("url_ratio", 0) > 0.4:
        hints.append(f"SCAM_BOT: {int(features.get('url_ratio',0)*100)}% of tweets contain external links — primary scam signal")
    if features.get("profile_completeness", 4) < 2 and features.get("tweet_count", 0) > 200:
        hints.append("SCAM_BOT: Highly active account with incomplete profile")

    # --- Cyborg ---
    if (
        features.get("profile_completeness", 0) >= 3
        and features.get("abnormal_velocity")
        and features.get("account_age_days", 0) > 365
        and not features.get("self_identifies_as_bot")
    ):
        hints.append("CYBORG: Established account with inhuman tweet velocity")
    if features.get("uses_suspicious_client"):
        hints.append(
            f"CYBORG: Tweets sent via suspicious third-party client: "
            f"{features.get('tweet_clients')}"
        )

    # --- Human signals ---
    if (
        features.get("account_age_days", 0) > 365
        and features.get("profile_completeness", 0) >= 3
        and not features.get("abnormal_velocity")
        and not features.get("highly_repetitive")
        and not features.get("url_heavy")
        and features.get("follower_ratio", 0) > 0.1
        and not features.get("keyword_flags")
    ):
        hints.append("HUMAN: Multiple authenticity signals present")

    return hints
