"""
score_all.py
Executes the scoring engine across all available locales and platforms in the metadata/ directory.
Produces a Global Score summary.
"""

import os
import glob
import subprocess
import re

def main():
    metadata_dir = "metadata"
    keywords_dir = "keywords"
    
    metadata_files = glob.glob(f"{metadata_dir}/*.yaml")
    
    if not metadata_files:
        print("No metadata files found.")
        return

    print("═══════════════════════════════════════════════════════")
    print("  AutoASO — Global Footprint Score")
    print("═══════════════════════════════════════════════════════\n")

    total_global_score = 0
    total_installs = 0
    count = 0
    
    for meta_path in metadata_files:
        filename = os.path.basename(meta_path)
        kw_path = os.path.join(keywords_dir, filename)
        
        if not os.path.exists(kw_path):
            print(f"Skipping {filename}: Matching keyword file missing.")
            continue
            
        # Run score.py
        result = subprocess.run(
            ["python3", "score.py", "--metadata", meta_path, "--keywords", kw_path],
            capture_output=True, text=True
        )
        
        output = result.stdout
        
        score_match = re.search(r"total_score:\s+([\d\.]+)", output)
        installs_match = re.search(r"est_installs:\s+([\d\.]+)", output)
        
        score = float(score_match.group(1)) if score_match else 0.0
        installs = float(installs_match.group(1)) if installs_match else 0.0
        
        print(f"[{filename.replace('.yaml','')}]")
        print(f"  Score:    {score:.2f}/100")
        print(f"  Installs: ~{installs:.0f}/mo\n")
        
        total_global_score += score
        total_installs += installs
        count += 1
        
    if count > 0:
        avg_score = total_global_score / count
        print("───────────────────────────────────────────────────────")
        print(f"GLOBAL AVERAGE SCORE:   {avg_score:.2f}/100")
        print(f"TOTAL EST. INSTALLS:    ~{total_installs:.0f}/mo")
        print("───────────────────────────────────────────────────────")

if __name__ == "__main__":
    main()
