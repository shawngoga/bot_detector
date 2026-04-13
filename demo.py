import asyncio
import os
from dotenv import load_dotenv
from scraper.twitter_scraper import TwitterScraper
from analyzer.feature_extractor import extract_features
from analyzer.claude_analyzer import analyze_account
from taxonomy.bot_classifier import rule_based_prescore
from attribution.attribution_engine import generate_attribution_report

load_dotenv()

DEMO_ACCOUNTS = [
    "elonmusk",
    "POTUS",
]

async def main():
    scraper = TwitterScraper()
    await scraper.login()

    for username in DEMO_ACCOUNTS:
        print(f"\n{'='*50}")
        print(f"Analyzing @{username}")
        profile     = await scraper.get_user_profile(username)
        features    = extract_features(profile)
        hints       = rule_based_prescore(profile, features)
        result      = analyze_account(profile, features, hints)
        attribution = generate_attribution_report(profile, features, result)
        print(f"Category:    {result['category']} ({int(result['confidence']*100)}%)")
        print(f"Verdict:     {result['verdict']}")
        print(f"Timezone:    {attribution['inferred_timezone']}")
        print(f"Skill level: {attribution['operator_skill']}")

asyncio.run(main())
