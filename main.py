import asyncio
import os
from dotenv import load_dotenv
from supabase import create_client

from scraper.twitter_scraper import TwitterScraper
from analyzer.feature_extractor import extract_features
from analyzer.claude_analyzer import analyze_account
from taxonomy.bot_classifier import rule_based_prescore
from network.graph_builder import build_edges_from_profile, detect_clusters
from attribution.attribution_engine import generate_attribution_report
from responder.reply_handler import format_reply, post_reply

load_dotenv()

# ── Supabase client ──────────────────────────
def get_supabase():
    return create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )

# ── Save full analysis to Supabase ───────────
def save_analysis(profile: dict, features: dict, result: dict):
    supabase = get_supabase()
    try:
        supabase.table("bot_analyses").insert({
            "username":               profile.get("username"),
            "user_id":                profile.get("user_id"),
            "category":               result.get("category"),
            "confidence":             result.get("confidence"),
            "signals":                result.get("primary_signals", []),
            "verdict":                result.get("verdict"),
            "account_age_days":       features.get("account_age_days"),
            "followers_count":        profile.get("followers_count"),
            "following_count":        profile.get("following_count"),
            "tweet_count":            profile.get("tweet_count"),
            "likes_given":            profile.get("likes_given"),
            "follower_ratio":         features.get("follower_ratio"),
            "tweets_per_day":         features.get("tweets_per_day"),
            "profile_completeness":   features.get("profile_completeness"),
            "has_profile_image":      features.get("has_profile_image"),
            "has_bio":                features.get("has_bio"),
            "verified":               profile.get("verified"),
            "tweet_client":           str(features.get("tweet_clients", [])),
            "self_identifies_as_bot": features.get("self_identifies_as_bot"),
            "stated_purpose":         features.get("stated_purpose"),
            "avg_tweet_length":       features.get("avg_tweet_length"),
            "content_unique_ratio":   features.get("content_unique_ratio"),
            "url_heavy":              features.get("url_heavy"),
            "keyword_flags":          features.get("keyword_flags", []),
            "broadcast_pattern":      features.get("broadcast_pattern"),
        }).execute()
        print(f"[+] Saved analysis for @{profile.get('username')}")
    except Exception as e:
        print(f"[-] Failed to save analysis: {e}")


# ── Full pipeline for one mention ────────────
async def process_mention(scraper: TwitterScraper, mention):
    username   = mention.user.screen_name
    mention_id = mention.id

    print(f"\n{'='*50}")
    print(f"[+] Analyzing @{username}")
    print(f"{'='*50}")

    # 1. Scrape
    profile = await scraper.get_user_profile(username)
    if not profile:
        print(f"[-] Could not fetch profile for @{username}")
        return

    # 2. Extract features
    features = extract_features(profile)
    print(f"[+] Features extracted — "
          f"age={features.get('account_age_days')}d | "
          f"tweets/day={features.get('tweets_per_day')} | "
          f"ratio={features.get('follower_ratio')}")

    # 3. Rule-based pre-score
    hints = rule_based_prescore(profile, features)
    print(f"[+] Pre-score hints: {hints if hints else 'none'}")

    # 4. Claude classification
    result = analyze_account(profile, features, hints)
    print(f"[+] Claude result: {result.get('category')} "
          f"({int(result.get('confidence', 0) * 100)}% confidence)")

    # 5. Save to Supabase
    save_analysis(profile, features, result)

    # 6. Build network edges
    build_edges_from_profile(profile, result.get("category"))

    # 7. Attribution report
    attribution = generate_attribution_report(
        profile=profile,
        features=features,
        claude_result=result,
        botnet_members=[]
    )
    print(f"[+] Attribution: timezone={attribution.get('inferred_timezone')} | "
          f"origin={attribution.get('likely_origin')} | "
          f"skill={attribution.get('operator_skill')}")

    # 8. Format and post reply
    reply_text = format_reply(username, result)
    print(f"[+] Reply:\n{reply_text}")
    await post_reply(scraper.client, reply_text, mention_id)

    # 9. Run cluster detection every 10 analyses
    supabase   = get_supabase()
    count      = supabase.table("bot_analyses").select("id", count="exact").execute()
    total      = count.count or 0
    if total % 10 == 0 and total > 0:
        print(f"\n[*] Running cluster detection ({total} accounts analyzed)...")
        detect_clusters()


# ── Main polling loop ────────────────────────
async def main():
    scraper     = TwitterScraper()
    seen_ids    = set()

    await scraper.login()
    print("[*] Bot detector running. Polling for mentions every "
          f"{os.getenv('POLL_INTERVAL', 60)}s...")

    while True:
        try:
            mentions = await scraper.get_mentions()

            if not mentions:
                print("[*] No new mentions.")
            else:
                for mention in mentions:
                    if mention.id not in seen_ids:
                        seen_ids.add(mention.id)
                        await process_mention(scraper, mention)

        except Exception as e:
            print(f"[-] Polling error: {e}")

        await asyncio.sleep(int(os.getenv("POLL_INTERVAL", 60)))


if __name__ == "__main__":
    asyncio.run(main())