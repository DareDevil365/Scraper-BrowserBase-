import sys
import os
import subprocess
from pathlib import Path

# Add workspace root to sys.path
scout_root = Path(r"c:\Users\yasha\Desktop\scout")
sys.path.append(str(scout_root))

from engine.persistence import get_session
from engine.session_output import write_final_synthesis, write_partial_final

session_id = "29cc7505"
output_folder = scout_root / "outputs" / "give_me_a_detailes_guide_for_a_beginner_who_wnats_to_learn_a_20260601094437_29cc7505"

print("Fetching session from database...")
session = get_session(session_id)
if not session:
    print(f"Error: Session {session_id} not found in database!")
    sys.exit(1)

print("Regenerating final synthesis and partial reports...")
# Write v1 report
if session.get("result_data"):
    write_final_synthesis(str(output_folder), session["result_data"], version="v1")
    write_final_synthesis(str(output_folder), session["result_data"], version="v2")

# Write partial report
if session.get("vector_results"):
    write_partial_final(str(output_folder), session, session["vector_results"])

print("Running presenter to rebuild DOCX and HTML reports...")
present_py = scout_root / "present.py"
import shutil

# Compile docx and html
subprocess.run(
    [sys.executable, str(present_py), str(output_folder), "--formats", "docx,html"],
    check=True
)

# Copy report.docx to report1.docx in workspace root
docx_src = output_folder / "report.docx"
docx_dest = scout_root / "report1.docx"
if docx_src.exists():
    print(f"Copying {docx_src.name} to {docx_dest}...")
    try:
        shutil.copy2(docx_src, docx_dest)
    except PermissionError:
        print("Warning: Permission denied when copying report.docx to report1.docx (it might be open in Word).")

# Copy report.html to report1.html in workspace root
html_src = output_folder / "report.html"
html_dest = scout_root / "report1.html"
if html_src.exists():
    print(f"Copying {html_src.name} to {html_dest}...")
    try:
        shutil.copy2(html_src, html_dest)
    except PermissionError:
        print("Warning: Permission denied when copying report.html to report1.html.")

print("Successfully regenerated all report files!")

