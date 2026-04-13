import os
import re
from collections import Counter
from datetime import datetime
from supabase import create_client


def get_supabase():
    return create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )


def infer_timezone(tweet_times: list) -> dict:
    if not tweet_times:
        return {"timezone": "unknown", "confidence": 0.0}

    hours = []
    for t in tweet_times:
        try:
            dt = datetime.fromisoformat(t.replace("Z", "+00:00"))
            hours.append(dt.hour)
        except Exception:
            continue

    if not hours:
        return {"timezone": "unknown", "confidence": 0.0}

    hour_counts = Counter(hours)
    peak_hour   = hour_counts.most_common(1)[0][0]

    timezone_map = {
        range(0, 3):   "UTC+0 (UK/West Africa)",
        range(3, 6):   "UTC+3 (East Africa/Middle East)",
        range(6, 9):   "UTC+6 (Central Asia)",
        range(9, 12):  "UTC+9 (East Asia/Japan/Korea)",
        range(12, 15): "UTC-12 to UTC-10 (Pacific Islands)",
        range(15, 18): "UTC-7 to UTC-5 (US Central/Eastern)",
        range(18, 21): "UTC-5 to UTC-3 (US East/South America)",
        range(21, 24): "UTC-2 to UTC+0 (Atlantic/UK)",
    }

    inferred_tz = "unknown"
    for hour_range, tz in timezone_map.items():
        if peak_hour in hour_range:
            inferred_tz = tz
            break

    top_3_hours = sum(v for _, v in hour_counts.most_common(3))
    confidence  = round(top_3_hours / len(hours), 2)

    return {
        "timezone":          inferred_tz,
        "peak_hour":         peak_hour,
        "confidence":        confidence,
        "hour_distribution": dict(hour_counts)
    }


def fingerprint_language(tweets: list) -> dict:
    if not tweets:
        return {}

    language_markers = {
        "russian_influence": ["провокация", "западный", "нато", "украина"],
        "chinese_influence": ["中国", "台湾", "香港", "共产党"],
        "iranian_influence": ["زندان", "آمریکا", "اسرائیل", "انقلاب"],
        "domestic_us":       ["maga", "deep state", "fake news", "trump", "biden"]
    }

    detected = []
    all_text  = " ".join(tweets).lower()

    for origin, markers in language_markers.items():
        if any(m in all_text for m in markers):
            detected.append(origin)

    phrases = []
    for tweet in tweets:
        words = tweet.split()
        for i in range(len(words) - 4):
            phrases.append(" ".join(words[i:i+5]))

    phrase_counts = Counter(phrases)
    repeated      = [p for p, c in phrase_counts.items() if c > 1]
    urls          = re.findall(r'https?://(?:www\.)?([^/\s]+)', all_text)
    domains       = Counter(urls)

    return {
        "likely_origin":    detected,
        "repeated_phrases": repeated[:5],
        "external_domains": dict(domains.most_common(5)),
        "operator_skill":   "high" if not repeated else "medium" if len(repeated) < 3 else "low"
    }


def cluster_infrastructure(botnet_members: list) -> dict:
    if not botnet_members:
        return {}

    supabase = get_supabase()
    data     = supabase.table("bot_analyses")\
        .select("username, account_age_days, tweet_clients, keyword_flags")\
        .in_("username", botnet_members)\
        .execute()

    if not data.data:
        return {}

    base_names = [re.sub(r'\d+$', '', r["username"]) for r in data.data]
    name_counts = Counter(base_names)
    sequential_bases = [n for n, c in name_counts.items() if c > 1]

    all_clients = []
    for record in data.data:
        all_clients.extend(record.get("tweet_clients") or [])
    shared_clients = Counter(all_clients).most_common(3)

    ages     = [r["account_age_days"] for r in data.data if r["account_age_days"]]
    age_var  = (max(ages) - min(ages)) if len(ages) > 1 else 0
    coordinated = age_var < 30

    return {
        "sequential_usernames":      sequential_bases,
        "shared_clients":            shared_clients,
        "coordinated_creation":      coordinated,
        "account_age_variance_days": age_var,
        "operator_count_estimate": (
            "likely single operator" if coordinated and sequential_bases
            else "possibly multiple operators"
        )
    }


def generate_attribution_report(
    profile:        dict,
    features:       dict,
    claude_result:  dict,
    botnet_members: list = []
) -> dict:
    username     = profile.get("username")
    tweet_times  = profile.get("recent_tweet_times", [])
    tweets       = profile.get("recent_tweets", [])

    tz_data      = infer_timezone(tweet_times)
    lang_data    = fingerprint_language(tweets)
    infra_data   = cluster_infrastructure(botnet_members) if botnet_members else {}
    claude_hints = claude_result.get("attribution_hints", {})

    report = {
        "username":             username,
        "category":             claude_result.get("category"),
        "confidence":           claude_result.get("confidence"),
        "inferred_timezone":    tz_data.get("timezone"),
        "peak_activity_hour":   tz_data.get("peak_hour"),
        "timezone_confidence":  tz_data.get("confidence"),
        "likely_origin":        lang_data.get("likely_origin", []),
        "repeated_phrases":     lang_data.get("repeated_phrases", []),
        "external_domains":     lang_data.get("external_domains", {}),
        "operator_skill":       lang_data.get("operator_skill"),
        "infrastructure":       infra_data,
        "claude_attribution":   claude_hints,
        "operator_profile": {
            "estimated_timezone":   tz_data.get("timezone", "unknown"),
            "estimated_origin":     lang_data.get("likely_origin", ["unknown"]),
            "skill_level":          claude_hints.get("operator_skill_level", "unknown"),
            "likely_motive":        claude_hints.get("likely_motive", "unknown"),
            "operator_count":       infra_data.get("operator_count_estimate", "unknown"),
            "infrastructure_notes": claude_hints.get("infrastructure_notes", "")
        }
    }

    supabase = get_supabase()
    supabase.table("attribution").insert({
        "signal_type":  "full_report",
        "signal_value": str(report),
        "confidence":   claude_result.get("confidence", 0.0),
        "notes":        str(report.get("operator_profile"))
    }).execute()

    return report
