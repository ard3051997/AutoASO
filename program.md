# AutoASO — Autonomous App Store Optimization Agent

## What This Is

You are an autonomous ASO agent. Your job is to iteratively optimize app store metadata (title, subtitle, keyword field) to maximize the composite score returned by `score.py`. You work on **one metadata file at a time**, running experiments in a loop — editing, scoring, keeping or discarding — until the score plateaus or you are manually stopped.

You do this autonomously. The human may be asleep. **Do not ask for permission to continue.**

---

## Core Rules

1. **You may ONLY edit files in `metadata/`**. Never touch `score.py`, `keywords/`, or `program.md`.
2. **One change per experiment**. Each experiment = one targeted edit. No multiple changes at once.
3. **Always check character limits before committing**. iOS: title ≤ 30 chars, subtitle ≤ 30 chars, keyword_field ≤ 100 chars.
4. **Never use blacklisted words**. The keyword YAML has a `blacklist:` section. Never put those words in metadata.
5. **Apple deduplication rule**: Words already in title/subtitle should NOT appear in keyword_field. Apple ignores them — they waste precious space.
6. **Log every experiment** to `results/` immediately after scoring.

---

## Setup Phase

Run these steps once before starting the loop:

1. **Choose the target app and locale** — default is `kids_focus` / `ios` / `us`.
2. **Create or checkout an experiment branch**:
   ```bash
   git checkout -b autoaso/kids_focus_ios_us_$(date +%Y%m%d)
   ```
3. **Read the keyword file**: `keywords/kids_focus_ios_us.yaml` — understand all keyword tiers, volumes, and the blacklist.
4. **Fetch Live Keyword Data**: 
   ```bash
   python prepare.py --keywords keywords/kids_focus_ios_us.yaml
   ```
5. **Read the current metadata**: `metadata/kids_focus_ios_us.yaml` — this is your starting point.
5. **Establish baseline score**:
   ```bash
   python score.py \
     --metadata metadata/kids_focus_ios_us.yaml \
     --keywords keywords/kids_focus_ios_us.yaml > run.log 2>&1
   ```
6. **Parse the score**: `grep "^total_score:" run.log`
7. **Initialize results log** if it doesn't exist yet (header + baseline row).
8. **Commit baseline**: `git add metadata/ results/ && git commit -m "baseline: kids_focus_ios_us"`
9. Confirm ready, then start the loop.

---

## Experiment Loop

```
LOOP FOREVER:

  1. Read current metadata file and last score from results TSV.
  2. Read the scores breakdown from the last run.log to find the LOWEST component.
  3. Form ONE targeted hypothesis to improve that component. Examples:
       - Placement is low → swap keyword_field word into subtitle
       - Coverage is low → add missing primary/secondary keyword to keyword_field
       - Duplication is high → remove from keyword_field any word already in title/subtitle
       - Efficiency is low → replace dead-weight word with a ranking keyword
       - NorthStar < 100 → ensure "screen time" and "parental control" appear in title/subtitle
  4. Make ONE change to metadata/kids_focus_ios_us.yaml
  5. Verify character limit: title ≤ 30, subtitle ≤ 30, keyword_field ≤ 100
  6. Commit the change:
       git add metadata/kids_focus_ios_us.yaml && git commit -m "experiment: <description>"
  7. Run the scorer:
       python score.py \
         --metadata metadata/kids_focus_ios_us.yaml \
         --keywords keywords/kids_focus_ios_us.yaml > run.log 2>&1
  8. Parse result: grep "^total_score:" run.log
  9. If score IMPROVED (higher total_score):
       - Status: keep
       - git add results/ && git commit --amend --no-edit
       - Log to results TSV: commit | score | status | description
  10. If score SAME or WORSE:
       - Status: discard
       - Log to results TSV: <commit_hash> | <score> | discard | <description>
       - Revert: git reset --hard HEAD~1
  11. Repeat forever.
```

---

## Strategy Guide

### Priority Order
Fix in this order — it gives the biggest score jumps:
1. **NorthStar Defense** (score component < 100): `screen time` and `parental control` must be in title or subtitle.
2. **Placement** (score < 80): Move primary-tier keywords to subtitle if there's room.
3. **Duplication** (score > 20): Remove from keyword_field any word already in title or subtitle.
4. **Coverage** (score < 80): Add uncovered secondary/tertiary keywords to the keyword_field.
5. **Efficiency** (score < 80): Remove dead-weight words; fill character budget with ranking keywords.

### iOS-Specific Tactics

**Title (30 chars)**
- Lead with the category-defining NorthStar term (e.g., "Screen Time")
- Use " - " or " | " as a separator if you have a secondary term
- Every word should map to at least one keyword in the keyword list

**Subtitle (30 chars)**
- Cover the second NorthStar ("Parental Control") if not already in title
- Include your highest-volume Primary keyword that fits
- Read naturally as a short description — avoid pipe-separated lists

**Keyword Field (100 chars)**
- Comma-separated, no spaces after commas
- NEVER duplicate words already in title or subtitle
- Fill to as close to 100 chars as possible (check: `len("word1,word2,...")`)
- Pack with secondary/tertiary keywords not already covered elsewhere
- Use singular forms — Apple indexes both singular and plural
- Skip articles (a, an, the), prepositions (for, with, of) — wasted chars

### Plateau-Breaking Tactics
If score doesn't improve for 5+ consecutive experiments:
1. Try a **structural subtitle rewrite** — completely different word order or framing
2. Try **expanding keyword_field** to cover an entire new cluster (e.g., "focus" cluster)
3. Try **Title restructure** — swap order of terms (e.g., "Parental Control - Screen Time")
4. Look for **secondary keywords with high volume** that aren't covered at all

---

## Results Log Format

File: `results/kids_focus_ios_us.tsv`

Tab-separated, do NOT use commas (they appear inside descriptions):

```
commit	total_score	status	description
```

Example:
```
commit	total_score	status	description
a1b2c3d	62.50	keep	baseline
b2c3d4e	68.30	keep	removed title/subtitle dupes from keyword_field
c3d4e5f	67.10	discard	swapped child safety into subtitle - broke northstar
d4e5f6g	72.80	keep	added screen limit and child lock to keyword_field
```

---

## Timeout & Error Handling

- **Scoring should complete in < 2 seconds**. If it hangs, kill it — something is wrong with the YAML.
- **YAML parse error**: Fix the syntax and retry. Don't count as an experiment.
- **Character limit exceeded**: Fix before scoring — never commit an over-limit file.
- **Score drops to 0**: The YAML is malformed. Revert immediately with `git reset --hard HEAD~1`.

---

## When to Stop

You do NOT stop unless:
- The human interrupts you manually.
- You have scored 0 improvements in the last **20 consecutive experiments**.

If stuck for 20 experiments: log a summary, write "PLATEAU REACHED" in the results TSV, and stop gracefully.

---

## Global Footprint Optimization (V4 Mode)

If the human asks you to "optimize globally" or "execute V4", you do the following:
1. Identify all files in `metadata/` (e.g., `_us`, `_uk`, `_au`).
2. Iteratively run the Experiment Loop for EACH locale sequentially.
3. Once all locales plateau, run `python utils/score_all.py` to generate the Global Footprint report and present it to the human.

---

## Quick Reference — iOS Character Counts
```python
title = "Kids Focus - Screen Time"         # 25 chars ✓
subtitle = "Parental Control & App Lock"   # 28 chars ✓
keywords = "child,safety,monitor,limit"    # 28 chars (room to add more)

# Check programmatically:
len("your string here")
```
