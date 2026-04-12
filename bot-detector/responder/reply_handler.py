def format_reply(username: str, result: dict) -> str:
    """Format bot detection result as a tweet reply."""

    category_labels = {
        "engagement_bot": "🤖 Engagement Bot",
        "influence_bot":  "🎭 Influence Bot",
        "scam_bot":       "⚠️ Scam Bot",
        "cyborg":         "🧬 Cyborg Account",
        "utility_bot":    "✅ Legitimate Bot",
        "human":          "👤 Likely Human",
        "unknown":        "❓ Inconclusive",
    }

    label          = category_labels.get(result.get("category", "unknown"), "❓ Unknown")
    confidence_pct = int((result.get("confidence", 0)) * 100)
    signals        = result.get("primary_signals", [])[:3]
    verdict        = result.get("verdict", "No verdict available.")

    reply = (
        f"@{username} Bot Detection Report:\n\n"
        f"{label} — {confidence_pct}% confidence\n\n"
        f"📋 {verdict}\n\n"
        f"🔍 Signals: {', '.join(signals)}"
    )

    # Twitter has a 280 character limit
    if len(reply) > 280:
        reply = reply[:277] + "..."

    return reply


async def post_reply(client, reply_text: str, mention_id: str):
    """Post the reply tweet."""
    try:
        await client.create_tweet(
            text=reply_text,
            reply_to=mention_id
        )
        print(f"[+] Reply posted successfully.")
    except Exception as e:
        print(f"[-] Failed to post reply: {e}")