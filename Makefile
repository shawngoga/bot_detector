# Bot Detector — Makefile
# Usage: make <command>

PYTHON = /usr/local/bin/python3.11
PIP = /usr/local/bin/python3.11 -m pip

.PHONY: install test run push convert-cookies clean help

help:
	@echo ""
	@echo "Bot Detector — Available Commands"
	@echo "=================================="
	@echo "make install         Install all dependencies"
	@echo "make convert-cookies Convert Cookie-Editor JSON to twikit format"
	@echo "make test            Test full pipeline against @twitter account"
	@echo "make run             Start the bot detector"
	@echo "make push            Commit and push to GitHub"
	@echo "make clean           Remove cache files"
	@echo ""

install:
	@echo "[*] Installing dependencies..."
	$(PIP) install twikit==2.1.3 anthropic supabase python-dotenv networkx pandas pyvis
	@echo "[+] Done"

convert-cookies:
	@echo "[*] Converting cookies.json to twikit format..."
	$(PYTHON) -c "\
import json; \
f = open('cookies.json'); \
c = json.load(f); \
f.close(); \
converted = {x['name']: x['value'] for x in c} if isinstance(c, list) else c; \
f = open('cookies.json', 'w'); \
json.dump(converted, f, indent=2); \
f.close(); \
print('[+] Cookies converted')"

test:
	@echo "[*] Testing pipeline against @twitter..."
	$(PYTHON) -c "\
import asyncio, os; \
from dotenv import load_dotenv; \
from scraper.twitter_scraper import TwitterScraper; \
from analyzer.feature_extractor import extract_features; \
from taxonomy.bot_classifier import rule_based_prescore; \
from analyzer.claude_analyzer import analyze_account; \
load_dotenv(); \
async def test(): \
    scraper = TwitterScraper(); \
    scraper.client.load_cookies('cookies.json'); \
    profile = await scraper.get_user_profile('twitter'); \
    features = extract_features(profile); \
    hints = rule_based_prescore(profile, features); \
    result = analyze_account(profile, features, hints); \
    print(f'[+] Category: {result[\"category\"]} ({int(result[\"confidence\"]*100)}%)'); \
    print(f'[+] Verdict: {result[\"verdict\"]}'); \
asyncio.run(test())"

run:
	@echo "[*] Starting bot detector..."
	$(PYTHON) main.py

push:
	@echo "[*] Pushing to GitHub..."
	git add .
	git commit -m "update"
	git push
	@echo "[+] Pushed"

clean:
	@echo "[*] Cleaning cache..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "[+] Clean"