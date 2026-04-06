# AutoASO

Autonomous App Store Optimization. An agent that iteratively improves app store metadata — titles, subtitles, and keyword fields — by running continuous experiments against a mathematically constrained composite scoring engine.

Inspired by [Karpathy's autoresearch](https://github.com/karpathy/autoresearch), which applies the same loop to ML hyperparameter search. AutoASO replaces the training script with an ASO scoring function, replaces model weights with app metadata, and incorporates live API constraints.

---

## Architecture

<p align="center">
  <img src="assets/architecture.png" alt="AutoASO optimization loop" width="640">
</p>

## The Core Concept

*One day, App Store Optimization used to be done by meat computers—human marketers staring at difficulty matrices on spreadsheets and guessing combinations. That era is fading. ASO is structurally becoming the domain of autonomous swarms of AI agents running endless optimizations in the skies overnight. This repo encodes the physics of the App Store algorithm into a local engine.*

The agent follows an unyielding protocol:
1. **Poll API:** Fetch latest competitive keyword search volume and difficulty from live sources (`prepare.py`).
2. **Diagnose:** Read current metadata configurations across all platforms.
3. **Hypothesize:** Attempt one targeted edit (e.g., swapping a high-difficulty phrase into a high-weight Title slot, breaking a duplicate penalty).
4. **Enforce Constants:** Reject immediately if Apple or Google Character limits are breached.
5. **Score & Evaluate:** Run the Simulated Ranking Physics engine. If the `total_score` and `est_installs` grow, Keep (`git commit`). If not, Discard (`git checkout`).
6. **Repeat forever.**

---

## Design Choices

- **Single file dependency**: The agent only edits deterministic `metadata/*.yaml` files. The optimizer constraints are completely untangled from the simulation engine.
- **Instant feedback loop**: Instead of a 5-minute training epoch limit, the "budget" here is an instant Python script mathematically bounded by iOS/Android character counts and penalty thresholds.
- **Self-contained Physics**: Runs directly on your machine without constantly incurring external API calls. Instead, it utilizes `prepare.py` once to download real-world constants, then locally simulates 1,000s of permutations against them. 

---

## How the Scoring Engine Works (V4 Architecture)

`score.py` compute a rigorous composite total using a combination of foundational Apple/Google indexing constraints combined with an advanced **Rank Position Simulator**. 

### 1. Simulated Keyword Ranking Engine (V2 Capability)
AutoASO has graduated from simple word-matching to predicting measurable product metrics:
- **Base Placement logic:** A keyword naturally aims for Rank 1 if placed in the Title, Rank 5 in Subtitles, etc.
- **Inverse Difficulty Penalties:** The `difficulty` rating (0-100) mathematically pushes the keyword down the list. A high-difficulty keyword buried in the `keyword_field` immediately drops past Rank 20.
- **Value-Driven Results:** Using historical CTR (Click-Through-Rate) step curves, the engine converts Simulated Rank directly into `est_installs`. If the agent cannot breach Rank ~10, installs remain `0/mo`. The AI is thus forced to hunt for asymmetric keyword combinations to drive revenue value.

### 2. Live API Polling (V3 Capability)
Instead of operating on static guesses, AutoASO ties to live infrastructure:
- **AppFollow Sync:** The `prepare.py` script leverages your `.env` `APPFOLLOW_API_KEY` to pull Search Volume and Difficulty directly from live markets.
- **Graceful Simulation:** If the API rate limits, the environment gracefully introduces a Gaussian random walk fluctuation (+/- 5%) keeping the environment physically dynamic for the agent overnight. 

### 3. Global Tier 1 Market Footprint (V4 Capability)
The system no longer stops at just US platforms. It acts as an autonomous global manager:
- Evaluates `_us`, `_uk`, `_au` for iOS, and `_gplay_us` for distinct Android constraints (like generating 2,000-character Long Descriptions balancing 5% density rules).
- Calculates the true portfolio power through `utils/score_all.py`.

### 4. Mathematical Heuristics Table
| Component | What It Measures |
|---|---|
| **V2 Simulation** | Simulated Rank predicting actual `est_installs` per month. (Heavy multiplier on total score). |
| Keyword Coverage | What percentage of target keywords appear anywhere in the metadata. |
| Placement Accuracy | A NorthStar keyword in the title is astronomically more valuable than the same word buried. |
| Character Efficiency | Utilization against character caps, tightly penalizing dead-weight UI words ("amazing", "best"). |
| Phrase Coverage | Checks if 3-word primary clusters remain completely contiguous. |
| Duplication Penalty | If iOS, duplicating words already in the Title into the Keyword field earns massive deductions. |

---

## Project Structure

```
score.py              — V2 Simulation & Scoring engine (read-only for the agent)
prepare.py            — V3 Live API connection / Keyword config prep
program.md            — Agent guidelines and workflow logic
requirements.txt      — Python dependencies

keywords/             — Search volume and difficulty configurations (prepped by API)
  kids_focus_ios_us.yaml
  kids_focus_gplay_us.yaml

metadata/             — App storefront configurations (Agent's ONLY playground)
  kids_focus_ios_us.yaml
  kids_focus_ios_uk.yaml

results/              — Nightly TSV tracking ledgers
utils/
  score_all.py        — Global footprint aggregation engine
```

---

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Prepare the Environment (Live Polling)
Connect `.env` and pull live traffic metrics before you deploy the agent:
```bash
python prepare.py --keywords keywords/kids_focus_ios_us.yaml
```

### 3. Evaluate the Global Footprint
To see the current health of all platforms simultaneously:
```bash
python utils/score_all.py
```

### 4. Deploy the Autonomous Swarm
Point any agentic runner (Claude Code, Cursor, Aider) directly at the project:
> *"Read `program.md`. Execute the V4 Global Footprint optimization overnight. Do not stop until all platforms hit a plateau."*

---

## Road Map

- [x] **V1** — Local scoring engine with manual keyword lists. iOS and Google Play heuristic support.
- [x] **V2** — Simulated keyword ranking model that estimates rank positioning and clicks. 
- [x] **V3** — API integration for live keyword volumes (AppFollow) ensuring rigorous training validity.
- [x] **V4** — Multi-locale scaling. Global evaluation aggregation across separate regional constraints.

---

## Acknowledgements

- Adapted structurally from Andrej Karpathy's [autoresearch](https://github.com/karpathy/autoresearch). AutoASO ports the overnight hyperparameter AI-optimization loop completely over to Organic Distribution frameworks. 
- Designed explicitly to bridge algorithmically robust App Store ranking factors against combinatorial LLM strengths.

---

## License

MIT
