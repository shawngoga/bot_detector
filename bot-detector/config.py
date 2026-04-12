import os
from dotenv import load_dotenv

load_dotenv()

# Twitter
TWITTER_USERNAME  = os.getenv("TWITTER_USERNAME")
TWITTER_EMAIL     = os.getenv("TWITTER_EMAIL")
TWITTER_PASSWORD  = os.getenv("TWITTER_PASSWORD")

# Claude
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL      = "claude-haiku-4-5-20251001"

# Supabase
SUPABASE_URL      = os.getenv("SUPABASE_URL")
SUPABASE_KEY      = os.getenv("SUPABASE_KEY")

# Settings
POLL_INTERVAL     = int(os.getenv("POLL_INTERVAL", 60))

# Thresholds
THRESHOLD_HIGH    = 0.70
THRESHOLD_MEDIUM  = 0.40

# Categories
CATEGORIES = [
    "engagement_bot",
    "influence_bot",
    "scam_bot",
    "cyborg",
    "utility_bot",
    "human"
]