import sys
import os
import json
from pathlib import Path

sys.path.append(os.path.abspath("."))
from engine import extractor
from engine import session_output
from engine.persistence import get_session
import subprocess

def load_keys():
    keys = []
    keys_file = "api_keys.txt"
    if os.path.exists(keys_file):
        with open(keys_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    keys.extend([k.strip() for k in line.split(",") if k.strip()])
    return ",".join(keys)

def main():
    keys = load_keys()
    print(f"Configuring extractor with {len(keys.split(','))} keys.")
    extractor.configure(keys)

    output_folder = r"outputs/what_exactly_is_an_escrow_account_difference_in_3pl_and_paym_20260602204305_0006da65"
    
    # Load session and vectors from database
    session = get_session("0006da65")
    if not session:
        print("Error: session not found in database.")
        return
        
    vectors = session.get("research_vectors", [])
    query = session.get("original_query", "")
    output_format = session.get("output_format", "docx")
    
    print(f"Loaded session with {len(vectors)} vectors.")
    print("Running synthesize_research_stream...")
    stream = extractor.synthesize_research_stream(
        vectors_data=[],
        original_query=query,
        format_hint=output_format,
        output_folder=output_folder,
        vectors=vectors
    )
    
    v1_path = os.path.join(output_folder, "final_report_v1.md")
    try:
        if os.path.exists(v1_path):
            os.remove(v1_path)
    except Exception as e:
        print("Could not remove old final_report_v1.md:", e)
        
    synthesis = None
    for chunk in stream:
        if isinstance(chunk, str):
            with open(v1_path, "a", encoding="utf-8") as f:
                f.write(chunk)
        else:
            synthesis = chunk
            
    if synthesis and isinstance(synthesis, dict) and synthesis.get("success", True):
        print("Writing final synthesis...")
        session_output.write_final_synthesis(output_folder, synthesis, version="v1")
        
        # Run present.py
        print("Running present.py...")
        present_py = Path("present.py").resolve()
        # present all formats (docx, html, pdf, xlsx)
        subprocess.run(
            [sys.executable, str(present_py), output_folder, "--formats", "docx,html,pdf,xlsx"],
            check=True
        )
        print("Regeneration completed successfully!")
    else:
        print("Synthesis failed or returned non-dict:", synthesis)

if __name__ == "__main__":
    main()
