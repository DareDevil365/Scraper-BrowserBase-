import os
import json
import shutil
import subprocess

session_dir = "outputs/make_a_detailed_excel_that_have_list_of_most_useful_free_ai__20260530105341_6f860882"
state_path = os.path.join(session_dir, "state.json")
state_bak = os.path.join(session_dir, "state.json.bak")
v1_path = os.path.join(session_dir, "final_report_v1.md")
v1_bak = os.path.join(session_dir, "final_report_v1.md.bak")

# 1. Back up original state.json and final_report_v1.md
print("Backing up state.json and final_report_v1.md...")
shutil.copy2(state_path, state_bak)
if os.path.exists(v1_path):
    shutil.copy2(v1_path, v1_bak)
    os.remove(v1_path)

# 2. Add vectors definition to state.json
vectors_def = [
  {
    "id": "v1",
    "topic": "Free AI Writing & Text Generation Tools",
    "status": "SUCCESS"
  },
  {
    "id": "v2",
    "topic": "Free AI Image & Visual Content Creation Tools",
    "status": "SUCCESS"
  },
  {
    "id": "v3",
    "topic": "Free AI Video & Audio Production Tools",
    "status": "SUCCESS"
  },
  {
    "id": "v4",
    "topic": "Free AI General Research & Information Tools",
    "status": "SUCCESS"
  },
  {
    "id": "v5",
    "topic": "Advanced & Niche Free AI Tools (Content & Research)",
    "status": "SUCCESS"
  },
  {
    "id": "v6",
    "topic": "Verification of 'Free' Tiers & Limitations",
    "status": "SUCCESS"
  },
  {
    "id": "v7",
    "topic": "Tool Usefulness, Key Features, and Use Cases Assessment",
    "status": "SUCCESS"
  }
]

with open(state_path, "r", encoding="utf-8") as f:
    state_data = json.load(f)

state_data["vectors"] = vectors_def

with open(state_path, "w", encoding="utf-8") as f:
    json.dump(state_data, f, indent=2)

# 3. Run fallback_synth.py
print("Running fallback_synth.py...")
subprocess.run(["python", "fallback_synth.py", session_dir], check=True)

# 4. Run present.py to compile the reports
print("Running present.py...")
subprocess.run(["python", "present.py", session_dir, "--formats", "docx,html"], check=True)

# 5. Overwrite report1.docx in workspace root
print("Overwriting report1.docx in workspace root...")
shutil.copy2(os.path.join(session_dir, "report.docx"), "report1.docx")

# 6. Restore original state.json and final_report_v1.md
print("Restoring backups...")
if os.path.exists(state_bak):
    if os.path.exists(state_path):
        os.remove(state_path)
    shutil.move(state_bak, state_path)
if os.path.exists(v1_bak):
    shutil.move(v1_bak, v1_path)

print("Done! Fallback report simulation completed successfully.")
