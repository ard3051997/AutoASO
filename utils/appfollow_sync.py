import os
import requests
import yaml
import json
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

APPFOLLOW_API_KEY = os.getenv("APPFOLLOW_API_KEY")

def fetch_appfollow_keywords(ext_id, device, country, language="en"):
    """
    Fetch keywords for a specific app from the AppFollow API.
    Note: Requires a valid AppFollow API key.
    """
    if not APPFOLLOW_API_KEY:
        print("Warning: APPFOLLOW_API_KEY not found in environment.")
        print("Using mock data structure for demonstration.")
        return get_mock_data(ext_id)

    url = "https://api.appfollow.io/v2/keywords"
    params = {
        "ext_id": ext_id,         # App ID (e.g. 123456789)
        "device": device,         # 'iphone' or 'android'
        "country": country,       # 'us', 'uk', etc.
        "language": language,     # 'en'
        "api_secret": APPFOLLOW_API_KEY
    }
    
    try:
        # Expected response structure check
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("keywords", [])
    except Exception as e:
        print(f"Error fetching from AppFollow: {e}")
        return []

def get_mock_data(ext_id):
    """Fallback mock data matching the AppFollow API structure."""
    return [
        {"kw": "screen time", "score": 82, "difficulty": 68, "pos": 2},
        {"kw": "parental control", "score": 78, "difficulty": 72, "pos": 4},
        {"kw": "app lock", "score": 58, "difficulty": 50, "pos": 15},
        {"kw": "child safety", "score": 38, "difficulty": 35, "pos": 22},
        {"kw": "digital wellbeing", "score": 20, "difficulty": 20, "pos": 50}
    ]

def categorize_keyword(kw_info):
    """Categorize a keyword into the 3D Framework tiers based on metrics."""
    score = kw_info.get("score", 0)       # AppFollow popularity/volume
    pos = kw_info.get("pos", 100)         # Current rank position
    
    if score >= 60 and pos <= 5:
        tier = "northstar"
    elif score >= 40:
        tier = "primary"
    elif score >= 25:
        tier = "secondary"
    else:
        tier = "tertiary"
        
    return {
        "keyword": kw_info.get("kw", ""),
        "tier": tier,
        "volume": score,
        "difficulty": kw_info.get("difficulty", 50),
        "cluster": "auto_assigned"
    }

def generate_yaml(app_name, platform, locale, keywords):
    """Generate the AutoASO keywords YAML format."""
    config = {
        "app": app_name,
        "platform": platform,
        "locale": locale,
        "keywords": [categorize_keyword(kw) for kw in keywords],
        "blacklist": [
            "amazing", "best", "cool", "awesome", "great", "top",
            "easy", "simple", "smart", "powerful", "ultimate", "perfect",
            "super", "leading", "premier"
        ]
    }
    
    output_filename = f"keywords/{app_name}_{platform}_{locale}.yaml"
    os.makedirs("keywords", exist_ok=True)
    
    with open(output_filename, 'w') as f:
        # Let's insert a header manually
        f.write(f"app: {app_name}\n")
        f.write(f"platform: {platform}\n")
        f.write(f"locale: {locale}\n\n")
        f.write("# ─────────────────────────────────────────────\n")
        f.write("# 3D Keyword Framework (Auto-generated via AppFollow Sync)\n")
        f.write("# ─────────────────────────────────────────────\n\n")
        f.write("keywords:\n")
        for kw in config["keywords"]:
            f.write(f"  - keyword: \"{kw['keyword']}\"\n")
            f.write(f"    tier: {kw['tier']}\n")
            f.write(f"    volume: {kw['volume']}\n")
            f.write(f"    difficulty: {kw['difficulty']}\n")
            f.write(f"    cluster: {kw['cluster']}\n\n")
            
        f.write("# ─────────────────────────────────────────────\n")
        f.write("# Dead-weight blacklist\n")
        f.write("# ─────────────────────────────────────────────\n")
        f.write("blacklist:\n")
        for word in config["blacklist"]:
            f.write(f"  - {word}\n")

    print(f"Successfully generated: {output_filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AppFollow Keyword Sync")
    parser.add_argument("--app", required=True, help="Internal app name (e.g. kids_focus)")
    parser.add_argument("--ext_id", required=True, help="App Store ID (e.g. 123456789)")
    parser.add_argument("--platform", required=True, choices=["ios", "android"], help="Platform")
    parser.add_argument("--locale", required=True, help="Locale (e.g. us, uk)")
    
    args = parser.parse_args()
    
    device = "iphone" if args.platform == "ios" else "android"
    
    print(f"Syncing keywords for {args.app} ({args.platform}/{args.locale}) from AppFollow...")
    raw_keywords = fetch_appfollow_keywords(args.ext_id, device, args.locale)
    
    if raw_keywords:
        generate_yaml(args.app, args.platform, args.locale, raw_keywords)
    else:
        print("No keywords retrieved.")
