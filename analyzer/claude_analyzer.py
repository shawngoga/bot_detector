import json
import os
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are an expert Twitter/X bot detection researcher for a cybersecurity project.
You classify accounts into exactly 6 categories:

1. ENGAGEMENT_BOT: Games X's recommendation engine via swarm-liking, automated
   bookmarking, and reply loops. Operates in coordinated botnets. High like-to-tweet
   ratio, follows other bots, engages abnormally early on posts.

2. INFLUENCE_BOT: Runs Coordinated Inauthentic Behavior (CIB) campaigns. Repeats
   key phrases to trend, follows predictable narratives, highly active, no nuance
   in views, coordinates with other accounts in timing and messaging.

3. SCAM_BOT: Financial extraction and PII harvesting. Link-heavy posts, targets
   high-follower reply sections, redirects off-platform, scam keywords, new accounts,
   impersonates verified users.

4. CYBORG: Human-operated account augmented with automation. Has genuine history
   but shows automation bursts. Uses third-party clients, posts at inhuman hours,
   alternates between nuanced and templated content.

5. UTILITY_BOT: LEGITIMATE automated account. Transparent about being a bot,
   serves a public function (weather, news, alerts). Do NOT flag as malicious.
   Consistent format, broadcast pattern, no manipulation signals.

6. HUMAN: Authentic individual. Natural posting patterns, varied content,
   genuine engagement, sleep gaps in activity, diverse topics.

RULES:
- High tweet volume alone does NOT mean malicious
- Templated content alone does NOT mean malicious
- Distinguish TRANSPARENT automation (utility) from COVERT automation (malicious)
- Base confidence on strength and number of signals present
- Always respond with valid JSON only. No text outside the JSON."""


def analyze_account(profile: dict, features: dict, hints: list) -> dict:
    user_prompt = f"""Analyze this Twitter/X account for bot behavior.

PROFILE DATA:
{json.dumps(profile, indent=2)}

EXTRACTED FEATURES:
{json.dumps(features, indent=2)}

PRE-SCORE HINTS (rule-based signals detected):
{chr(10).join(hints) if hints else "No strong rule-based signals detected."}

Classify this account. Return ONLY this JSON:
{{
  "category": "engagement_bot | influence_bot | scam_bot | cyborg | utility_bot | human",
  "confidence": 0.0,
  "primary_signals": ["signal1", "signal2", "signal3"],
  "reasoning": "One paragraph explaining your classification decision.",
  "verdict": "One sentence suitable for a public reply tweet.",
  "attribution_hints": {{
    "likely_timezone": "inferred timezone from posting times or language",
    "operator_skill_level": "low | medium | high",
    "likely_motive": "financial | political | social | unknown",
    "infrastructure_notes": "any notes on tools or clients used"
  }}
}}"""

    response = client.messages.create(
        model=os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001"),
        max_tokens=800,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}]
    )

    raw = response.content[0].text.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        clean = raw.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            return {
                "category":        "unknown",
                "confidence":      0.0,
                "primary_signals": ["Parse error"],
                "reasoning":       raw,
                "verdict":         "Analysis could not be completed.",
                "attribution_hints": {}
            }
