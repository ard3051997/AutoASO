"""
AutoASO Scoring Engine — READ-ONLY for the agent.

This file takes a metadata YAML and a keyword YAML and returns a
composite score out of 100. The agent is NOT allowed to edit this file.
It can ONLY edit the metadata/*.yaml files.

Usage:
    python score.py --metadata metadata/kids_focus_ios_us.yaml \
                    --keywords keywords/kids_focus_ios_us.yaml

Output (mirrors autoresearch format):
    ---
    total_score:     87.30
    coverage:        92.00
    placement:       85.00
    efficiency:      88.50
    phrase_coverage: 75.00
    duplication:     5.00
    northstar:       100.00
    naturalness:     82.00
    platform:        ios
    locale:          us
    char_usage:      title=28/30 subtitle=29/30 keywords=98/100
"""

import argparse
import re
import sys

import yaml

# ---------------------------------------------------------------------------
# Scoring Weights (read-only)
# ---------------------------------------------------------------------------

WEIGHTS = {
    "coverage":        0.25,
    "placement":       0.20,
    "efficiency":      0.15,
    "phrase_coverage": 0.10,
    "duplication":     0.05,   # penalty — higher duplication = lower score
    "northstar":       0.10,
    "naturalness":     0.05,
    "density":         0.10,
}

# Dead-weight words that contribute zero ranking signal
DEAD_WEIGHT_WORDS = {
    "amazing", "best", "cool", "awesome", "great", "top", "free",
    "new", "good", "easy", "simple", "fast", "quick", "smart",
    "powerful", "useful", "super", "ultimate", "perfect",
    "number", "one", "leading", "premier", "pro", "plus",
}

# iOS character limits per field
IOS_LIMITS = {
    "title":         30,
    "subtitle":      30,
    "keyword_field": 100,
}

# Google Play character limits per field
GPLAY_LIMITS = {
    "title":             30,
    "short_description": 80,
    "long_description":  4000,
}

# Field weights for placement scoring
IOS_FIELD_WEIGHTS = {
    "title":         5.0,
    "subtitle":      3.0,
    "keyword_field": 1.0,
}

GPLAY_FIELD_WEIGHTS = {
    "title":             5.0,
    "short_description": 3.0,
    "long_description":  1.0,
}

TIER_FIELD_REQUIREMENTS = {
    "ios": {
        "northstar": ["title", "subtitle"],       # Must appear in title OR subtitle
        "primary":   ["title", "subtitle", "keyword_field"],  # Should appear in title/subtitle/keywords
        "secondary": ["subtitle", "keyword_field"],
        "tertiary":  ["keyword_field"],
    },
    "gplay": {
        "northstar": ["title", "short_description"],
        "primary":   ["title", "short_description", "long_description"],
        "secondary": ["short_description", "long_description"],
        "tertiary":  ["long_description"],
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    """Lowercase and strip punctuation for keyword matching."""
    return re.sub(r"[^a-z0-9 ]", " ", text.lower()).strip()


def get_all_text(metadata: dict, platform: str) -> dict[str, str]:
    """Return a dict of {field_name: normalized_text} for all metadata fields."""
    if platform == "ios":
        return {
            "title":         normalize(metadata.get("title", "")),
            "subtitle":      normalize(metadata.get("subtitle", "")),
            "keyword_field": normalize(metadata.get("keyword_field", "").replace(",", " ")),
        }
    else:  # gplay
        return {
            "title":             normalize(metadata.get("title", "")),
            "short_description": normalize(metadata.get("short_description", "")),
            "long_description":  normalize(metadata.get("long_description", "")),
        }


def keyword_in_field(kw: str, field_text: str) -> bool:
    """Check if the full keyword phrase appears in the field text."""
    kw_norm = normalize(kw)
    return kw_norm in field_text


def get_char_limits(platform: str) -> dict:
    return IOS_LIMITS if platform == "ios" else GPLAY_LIMITS


def get_field_weights(platform: str) -> dict:
    return IOS_FIELD_WEIGHTS if platform == "ios" else GPLAY_FIELD_WEIGHTS


# ---------------------------------------------------------------------------
# Scoring Components
# ---------------------------------------------------------------------------

def score_coverage(keywords: list, fields: dict) -> float:
    """
    Keyword Coverage (25%): What % of all target keywords appear anywhere
    in the metadata? Weighted by tier.
    """
    tier_weights = {"northstar": 4.0, "primary": 2.0, "secondary": 1.0, "tertiary": 0.5}

    total_weight = 0.0
    covered_weight = 0.0
    all_text = " ".join(fields.values())

    for kw_entry in keywords:
        kw   = kw_entry["keyword"]
        tier = kw_entry.get("tier", "tertiary")
        w    = tier_weights.get(tier, 0.5)
        total_weight += w
        if keyword_in_field(kw, all_text):
            covered_weight += w

    if total_weight == 0:
        return 100.0
    return round((covered_weight / total_weight) * 100, 2)


def score_placement(keywords: list, fields: dict, platform: str) -> float:
    """
    Placement Accuracy (25%): Are keywords in their ideal fields?
    NorthStars must be in the highest-weight fields.
    """
    requirements = TIER_FIELD_REQUIREMENTS[platform]
    field_weights = get_field_weights(platform)

    tier_weights = {"northstar": 4.0, "primary": 2.0, "secondary": 1.0, "tertiary": 0.5}

    total_weight  = 0.0
    placed_weight = 0.0

    for kw_entry in keywords:
        kw          = kw_entry["keyword"]
        tier        = kw_entry.get("tier", "tertiary")
        kw_w        = tier_weights.get(tier, 0.5)
        ideal_fields = requirements.get(tier, list(fields.keys()))

        total_weight += kw_w

        # Find best field where this keyword appears among its ideal fields
        # weighted by field importance
        best_field_score = 0.0
        for field in ideal_fields:
            if field in fields and keyword_in_field(kw, fields[field]):
                fw = field_weights.get(field, 1.0)
                max_fw = max(field_weights.get(f, 1.0) for f in ideal_fields)
                best_field_score = max(best_field_score, fw / max_fw)

        placed_weight += kw_w * best_field_score

    if total_weight == 0:
        return 100.0
    return round((placed_weight / total_weight) * 100, 2)


def score_efficiency(metadata: dict, platform: str) -> float:
    """
    Character Efficiency (15%): How well are characterbudgets used?
    Dead-weight words are penalized.
    """
    limits = get_char_limits(platform)
    scores = []

    fields_to_check = ["title", "subtitle", "keyword_field"] if platform == "ios" else \
                      ["title", "short_description", "long_description"]

    for field in fields_to_check:
        if field not in metadata or field not in limits:
            continue
        raw = metadata.get(field, "")
        if not raw:
            scores.append(0.0)
            continue

        # Character utilization with strict targets
        char_used = len(raw)
        char_limit = limits[field]
        
        utilization = min(char_used / char_limit, 1.0)
        
        # Stringent Length Penalties (From ASOScorer Benchmarks)
        if field == "title" and char_used < 25:
            utilization *= 0.8  # Penalty for not maximizing title space
        if platform == "gplay" and field == "long_description":
            if char_used < 500:
                utilization *= 0.2
            elif char_used < 2000:
                utilization *= 0.7  # Target is 2000+ chars
        
        # Dead-weight penalty
        words = normalize(raw).split()
        dead = sum(1 for w in words if w in DEAD_WEIGHT_WORDS)
        dead_ratio = dead / max(len(words), 1)
        dead_penalty = dead_ratio * 0.5   # up to 50% penalty for all dead words

        field_score = utilization * (1 - dead_penalty) * 100
        scores.append(field_score)

    if not scores:
        return 100.0
    return round(sum(scores) / len(scores), 2)


def score_density(metadata: dict, keywords: list) -> float:
    """
    Keyword Density (10%): Optimal density is 3-5%.
    Too low or too high stuffing is penalized.
    (Derived from user's ASOScorer benchmarks)
    """
    # Combine all text
    all_text = " ".join(normalize(str(v)) for k, v in metadata.items() if k in ["title", "subtitle", "keyword_field", "short_description", "long_description"])
    words = all_text.split()
    total_words = len(words)
    
    if total_words == 0:
        return 0.0

    # Count matching keyword phrases
    kw_hits = 0
    for kw_entry in keywords:
        kw = normalize(kw_entry["keyword"])
        kw_len = len(kw.split())
        # Simplistic sliding window count for exact phrase matches
        for i in range(len(words) - kw_len + 1):
            if " ".join(words[i:i+kw_len]) == kw:
                kw_hits += kw_len # Count total words occupied by keywords
                
    density = (kw_hits / total_words) * 100

    # Benchmark: 2% min, 3-5% optimal, > 8% penalty
    if 3.0 <= density <= 5.0:
        return 100.0
    elif 2.0 <= density < 3.0:
        return 80.0
    elif density < 2.0:
        return (density / 2.0) * 80  # Scale up to 80
    elif density > 8.0:
        # High penalty for keyword stuffing
        excess = density - 5.0
        return max(100.0 - (excess * 15), 0.0)
    else: # 5.0 < density <= 8.0
        excess = density - 5.0
        return max(100.0 - (excess * 8), 0.0)


def score_phrase_coverage(keywords: list, fields: dict) -> float:
    """
    Phrase Coverage (10%): Multi-word keywords must appear as complete phrases,
    not just split across fields.
    Only scores multi-word keywords.
    """
    multi_word = [kw for kw in keywords if " " in kw["keyword"]]
    if not multi_word:
        return 100.0

    tier_weights = {"northstar": 4.0, "primary": 2.0, "secondary": 1.0, "tertiary": 0.5}
    total_weight   = 0.0
    covered_weight = 0.0
    all_text = " ".join(fields.values())

    for kw_entry in multi_word:
        kw   = kw_entry["keyword"]
        tier = kw_entry.get("tier", "tertiary")
        w    = tier_weights.get(tier, 0.5)
        total_weight += w
        if normalize(kw) in all_text:
            covered_weight += w

    if total_weight == 0:
        return 100.0
    return round((covered_weight / total_weight) * 100, 2)


def score_duplication(metadata: dict, platform: str) -> float:
    """
    Duplication penalty (10%): Returns PENALTY SCORE (0 = no duplication, 100 = all duplicates).
    The main scorer inverts this: contribution = weight * (100 - duplication_score)
    On iOS: Apple ignores duplicate words across fields — they waste precious space.
    """
    if platform == "ios":
        # iOS: words in title/subtitle should NOT appear in keyword_field
        title_words    = set(normalize(metadata.get("title", "")).split())
        subtitle_words = set(normalize(metadata.get("subtitle", "")).split())
        kw_words       = set(normalize(metadata.get("keyword_field", "").replace(",", " ")).split())

        # Cross-field duplicates between keyword_field and title/subtitle
        cross_dupes = kw_words & (title_words | subtitle_words)
        total_kw_words = len(kw_words) if kw_words else 1
        penalty = (len(cross_dupes) / total_kw_words) * 100
        return round(min(penalty, 100), 2)
    else:
        # Google Play: within-field repetition in long description
        long_desc = normalize(metadata.get("long_description", ""))
        words = long_desc.split()
        if not words:
            return 0.0
        from collections import Counter
        counts  = Counter(words)
        repeats = sum(max(0, c - 2) for w, c in counts.items() if w not in DEAD_WEIGHT_WORDS)
        penalty = min((repeats / max(len(words), 1)) * 200, 100)
        return round(penalty, 2)


def score_northstar(keywords: list, fields: dict, platform: str) -> float:
    """
    NorthStar Defense (10%): Each NorthStar keyword must appear in a high-value field.
    Binary per keyword: either it's defended or it's not.
    """
    northstars = [kw for kw in keywords if kw.get("tier") == "northstar"]
    if not northstars:
        return 100.0

    ideal_fields = TIER_FIELD_REQUIREMENTS[platform]["northstar"]
    defended = 0
    for kw_entry in northstars:
        kw = kw_entry["keyword"]
        for field in ideal_fields:
            if field in fields and keyword_in_field(kw, fields[field]):
                defended += 1
                break

    return round((defended / len(northstars)) * 100, 2)


def score_naturalness(metadata: dict, platform: str) -> float:
    """
    Semantic Naturalness (5%): A heuristic check that metadata reads naturally.
    Penalizes comma-stuffed titles, all-caps, and repetitive sentence structures.
    """
    score = 100.0
    fields_to_check = ["title", "subtitle"] if platform == "ios" else ["title", "short_description"]

    for field in fields_to_check:
        raw = metadata.get(field, "")
        if not raw:
            continue

        # Penalty: all-cap words (shouting)
        words = raw.split()
        caps_ratio = sum(1 for w in words if w.isupper() and len(w) > 2) / max(len(words), 1)
        score -= caps_ratio * 20

        # Penalty: starts with a verb (OK for CTAs but bad for titles)
        # Skip — too hard to detect without NLP

        # Penalty: ends with a comma, pipe, or dash (truncation artifacts)
        if raw.strip()[-1] in ",|-":
            score -= 10

        # Penalty: more than 2 special separators suggests keyword stuffing
        separators = sum(1 for c in raw if c in "|-&+")
        if separators > 2:
            score -= 10

    return round(max(score, 0), 2)


# ---------------------------------------------------------------------------
# Character Usage Report
# ---------------------------------------------------------------------------

def char_usage(metadata: dict, platform: str) -> str:
    limits = get_char_limits(platform)
    parts = []
    for field, limit in limits.items():
        raw = metadata.get(field, "")
        used = len(raw)
        parts.append(f"{field}={used}/{limit}")
    return "  ".join(parts)


# ---------------------------------------------------------------------------
# Main Scorer
# ---------------------------------------------------------------------------

def compute_score(metadata: dict, keywords: list, platform: str) -> dict:
    fields      = get_all_text(metadata, platform)
    coverage    = score_coverage(keywords, fields)
    placement   = score_placement(keywords, fields, platform)
    efficiency  = score_efficiency(metadata, platform)
    phrase_cov  = score_phrase_coverage(keywords, fields)
    duplication = score_duplication(metadata, platform)
    northstar   = score_northstar(keywords, fields, platform)
    naturalness = score_naturalness(metadata, platform)
    density     = score_density(metadata, keywords)

    # Duplication is a penalty — we invert it in the total
    total = (
        WEIGHTS["coverage"]        * coverage +
        WEIGHTS["placement"]       * placement +
        WEIGHTS["efficiency"]      * efficiency +
        WEIGHTS["phrase_coverage"] * phrase_cov +
        WEIGHTS["duplication"]     * (100 - duplication) +
        WEIGHTS["northstar"]       * northstar +
        WEIGHTS["naturalness"]     * naturalness +
        WEIGHTS["density"]         * density
    )

    return {
        "total_score":      round(total, 2),
        "coverage":         coverage,
        "placement":        placement,
        "efficiency":       efficiency,
        "phrase_coverage":  phrase_cov,
        "duplication":      duplication,
        "northstar":        northstar,
        "naturalness":      naturalness,
        "density":          density,
        "char_usage":       char_usage(metadata, platform),
        "platform":         platform,
        "locale":           metadata.get("locale", "unknown"),
    }


def print_score(result: dict):
    """Print score in the autoresearch-style format."""
    print("---")
    print(f"total_score:      {result['total_score']:.2f}")
    print(f"coverage:         {result['coverage']:.2f}")
    print(f"placement:        {result['placement']:.2f}")
    print(f"efficiency:       {result['efficiency']:.2f}")
    print(f"phrase_coverage:  {result['phrase_coverage']:.2f}")
    print(f"duplication:      {result['duplication']:.2f}")
    print(f"northstar:        {result['northstar']:.2f}")
    print(f"naturalness:      {result['naturalness']:.2f}")
    print(f"density:          {result['density']:.2f}")
    print(f"platform:         {result['platform']}")
    print(f"locale:           {result['locale']}")
    print(f"char_usage:       {result['char_usage']}")


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AutoASO Scorer")
    parser.add_argument("--metadata", required=True, help="Path to metadata YAML file")
    parser.add_argument("--keywords", required=True, help="Path to keyword YAML file")
    args = parser.parse_args()

    try:
        with open(args.metadata) as f:
            metadata = yaml.safe_load(f)
        with open(args.keywords) as f:
            kw_data = yaml.safe_load(f)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    platform = metadata.get("platform", kw_data.get("platform", "ios"))
    keywords = kw_data.get("keywords", [])

    result = compute_score(metadata, keywords, platform)
    print_score(result)
