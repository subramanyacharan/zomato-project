import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(r"c:\Users\Hp\Documents\projects\milestone 1")

def run_script(script_path: str, args: list[str]):
    cmd = [sys.executable, str(PROJECT_ROOT / script_path)] + args
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FAILED: {result.stderr}")
        sys.exit(1)
    print(f"SUCCESS: {result.stdout[:500]}")
    return json.loads(result.stdout)

payload = {
    "location": "Bellandur",
    "budget": "high",
    "cuisine": None,
    "minimum_rating": 4.0,
    "additional_preferences": []
}

with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json") as tf:
    json.dump(payload, tf)
    temp_input_path = tf.name

print(f"Temp file: {temp_input_path}")

try:
    print("--- Phase 3 ---")
    p3 = run_script("phase3_preference_collection/src/main.py", ["--input", temp_input_path])
    
    print("--- Phase 4 ---")
    p4 = run_script("phase4_candidate_filtering/src/main.py", ["--top-n", "5"])
    
    print("--- Phase 5 ---")
    p5 = run_script("phase5_llm_ranking/src/main.py", ["--top-n", "5"])
    
    print("ALL DONE!")
finally:
    if os.path.exists(temp_input_path):
        os.remove(temp_input_path)
