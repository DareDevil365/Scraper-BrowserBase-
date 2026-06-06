import os
from pathlib import Path

run_dir = Path("outputs/google_drive_business_plan_pricing_20260606024809_d6969252")
print("run_dir exists:", run_dir.exists())
print("run_dir absolute path:", run_dir.resolve())
if run_dir.exists():
    print("Files in run_dir:")
    for p in run_dir.iterdir():
        print(f"  - {p.name}: exists={p.exists()}")
