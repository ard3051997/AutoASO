# AutoASO

**AutoASO** is an autonomous App Store Optimization (ASO) agent that iteratively improves app metadata to maximize discovery and organic installs. 

Modeled after machine learning training loops, AutoASO runs continuous experiments on app titles, subtitles, and keywords. It edits metadata, scores the changes against a sophisticated composite scoring engine, keeps improvements, discards regressions, and iterates indefinitely until your ASO score plateaus.

---

## 🚀 How It Works

The core philosophy of AutoASO is: **Edit → Score → Validate → Repeat**.

The agent is the loop itself, and there's no central orchestrator required. It follows a provided set of instructions (`program.md`), edits the target metadata YAML files, runs the scoring engine (`score.py`), and logs its results.

1. **Analyze**: Identify the weakest ranking component from the last scoring run.
2. **Hypothesize**: Predict that a specific keyword swap or shift will improve the score.
3. **Execute**: Make a targeted edit to the metadata.
4. **Validate**: Check that constraints (like character limits) are respected.
5. **Score**: Run the evaluation engine.
6. **Decision**:
   - **Better Score** → Keep change (`git commit`).
   - **Worse Score** → Discard change (`git reset`).

---

## 🎯 The Scoring Engine
The `score.py` script computes a Composite Score (out of 100) based on 7 weighted factors:

| Component | Weight | Description |
|-----------|--------|-------------|
| **Keyword Coverage** | 25% | Percentage of target keywords covered across all fields, weighted by keyword tier. |
| **Placement Accuracy** | 25% | Heavy reward for placing high-value keywords in the most indexed fields (e.g., Title/Subtitle). |
| **Character Efficiency** | 15% | Measures character budget utilization (e.g., Apple's 30/30/100 limit) and penalizes dead-weight words like "amazing". |
| **Phrase Coverage** | 10% | Ensure multi-word keyword phrases appear continuously instead of arbitrarily broken. |
| **Duplication Penalty** | 10% | Heavily penalizes repeating identical words across fields (particularly relevant for Apple App Store). |
| **NorthStar Defense** | 10% | Binary check ensuring that your core defining category keywords strictly appear in the Title or Subtitle. |
| **Semantic Naturalness** | 5% | A readability check preventing keyword stuffing or excessive capitalization/punctuation. |

---

## 📚 The 3D Keyword Framework
Your keyword strategy is stored in `keywords/` and organized into tiered data:

- **NorthStar**: The foundational, category-defining terms for the app.
- **Primary**: High-intent, top-level keyword phrases.
- **Secondary**: Medium-volume keywords ideal for descriptive fields.
- **Tertiary**: Niche, descriptive terms used to pack keyword fields.

---

## 🛠️ Project Structure

```bash
score.py              # Main scoring engine (Read-only for agents)
program.md            # Default instruction protocol for the agent
requirements.txt      # Python dependencies
utils/report.py       # Helper script to generate performance reports

# Data Directories
keywords/             # Keyword definition files (Read-only for agents)
  └── kids_focus_ios_us.yaml

metadata/             # Active metadata (The ONLY files the agent edits)
  └── kids_focus_ios_us.yaml

results/              # TSV experiment logs tracking history
  └── kids_focus_ios_us.tsv
```

---

## 💻 Quick Start

### 1. Identify Environment & Install Dependencies
Requires Python 3.
```bash
pip install -r requirements.txt
```

### 2. Establish a Baseline
Run a baseline test using the initial metadata file to see the starting score.
```bash
python score.py \
  --metadata metadata/kids_focus_ios_us.yaml \
  --keywords keywords/kids_focus_ios_us.yaml
```

### 3. Run the Agent
Point your autonomous coding assistant (like Claude Code, GitHub Copilot, or an extended LLM runner) at your target configuration with `program.md`:

_Example Prompt:_
> "Read `program.md` and start executing the optimization experiment loop for kids_focus/ios/us."

### 4. Monitor Progress
You can view a clean report of the agent's progress over time:
```bash
python utils/report.py
```

---

## 🤝 Credits & Acknowledgements
- **[autoresearch](https://github.com/karpathy/autoresearch)**: The entire structural inspiration for AutoASO comes from Andrej Karpathy's `autoresearch` project, directly adapting the autonomous ML experiment loop logic for App Store Optimization. 
