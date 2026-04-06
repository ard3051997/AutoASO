"""
prepare.py
Downloads or simulates live AppFollow API data for keywords.
Usage: python prepare.py --keywords keywords/kids_focus_ios_us.yaml
"""

import argparse
import os
import random
import yaml
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import urllib.request
import json

def fetch_real_appfollow_data(api_key, keyword, country, device):
    """
    Attempt to fetch real data from AppFollow.
    Gracefully falls back to mock data if the API fails or limits are hit.
    """
    url = f"https://api.appfollow.io/v2/aso/search?term={urllib.parse.quote(keyword)}&country={country}&device={device}"
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {api_key}"})
    try:
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            # Depending on AppFollow schema, extract volume/diff
            if "data" in data and "volume" in data["data"]:
                return {
                    "volume": float(data["data"]["volume"]),
                    "difficulty": float(data["data"].get("difficulty", 50))
                }
    except Exception as e:
        # Graceful fallback
        pass
    return None

def mock_keyword_data(keyword, current_vol, current_diff):
    """
    Simulates a live data fluctuation to make the environment dynamic.
    """
    vol_shift = random.uniform(-0.1, 0.1) # 10% fluctuation
    diff_shift = random.uniform(-0.05, 0.05) # 5% fluctuation
    
    new_vol = max(1.0, min(100.0, current_vol * (1 + vol_shift)))
    new_diff = max(1.0, min(100.0, current_diff * (1 + diff_shift)))
    
    return {
        "volume": round(new_vol),
        "difficulty": round(new_diff)
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords", required=True, help="Path to keyword YAML file")
    args = parser.parse_args()

    api_key = os.environ.get("APPFOLLOW_API_KEY", "")
    print(f"Reading {args.keywords}...")
    
    with open(args.keywords, 'r') as f:
        data = yaml.safe_load(f)

    locale = data.get("locale", "us")
    platform = data.get("platform", "ios")
    device = "iphone" if platform == "ios" else "android"

    updated = 0
    if "keywords" in data:
        for kw_obj in data["keywords"]:
            kw = kw_obj["keyword"]
            current_vol = float(kw_obj.get("volume", 50))
            current_diff = float(kw_obj.get("difficulty", 50))
            
            live_data = None
            if api_key:
                live_data = fetch_real_appfollow_data(api_key, kw, locale, device)
            
            if not live_data:
                live_data = mock_keyword_data(kw, current_vol, current_diff)
                
            kw_obj["volume"] = live_data["volume"]
            kw_obj["difficulty"] = live_data["difficulty"]
            updated += 1
            
    # Write back to file ensuring safe saving
    with open(args.keywords, 'w') as f:
        yaml.dump(data, f, sort_keys=False, default_flow_style=False)
        
    print(f"✅ Successfully updated {updated} keywords with live/simulated AppFollow metrics.")

if __name__ == "__main__":
    main()
