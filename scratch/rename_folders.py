import os
import sqlite3
import shutil

db_path = "scout_results.db"
outputs_dir = r"c:\Users\yasha\Desktop\scout\outputs"

folders_config = [
    {
        "id": "0006da65",
        "old_name": "what_exactly_is_an_escrow_account_difference_in_3pl_and_paym_20260602204305_0006da65",
        "new_name": "what_exactly_is_an_escrow_account_difference_in_3pl_and_paym_20260602204305_0006da65_browserbase",
    },
    {
        "id": "f52b5d53",
        "old_name": "what_exactly_is_an_escrow_account_difference_in_3pl_and_paym_20260602021842_f52b5d53",
        "new_name": "what_exactly_is_an_escrow_account_difference_in_3pl_and_paym_20260602021842_f52b5d53_original",
    }
]

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

for cfg in folders_config:
    old_path = os.path.join(outputs_dir, cfg["old_name"])
    new_path = os.path.join(outputs_dir, cfg["new_name"])
    
    # Check if folder needs renaming
    if os.path.exists(old_path):
        print(f"Renaming folder on disk:\n  From: {old_path}\n  To:   {new_path}")
        try:
            shutil.move(old_path, new_path)
            print("  Disk rename: SUCCESS")
        except Exception as e:
            print(f"  Disk rename: FAILED ({e})")
            continue
    else:
        print(f"Folder already renamed or not found: {old_path}")
        
    # Now update SQLite
    cursor.execute("SELECT output_folder, output_file_path FROM research_sessions WHERE id = ?", (cfg["id"],))
    row = cursor.fetchone()
    if row:
        db_folder, db_file = row
        new_db_folder = os.path.join(outputs_dir, cfg["new_name"])
        new_db_file = None
        if db_file:
            new_db_file = db_file.replace(cfg["old_name"], cfg["new_name"])
            
        print(f"Updating database for session {cfg['id']}:")
        print(f"  output_folder: {new_db_folder}")
        print(f"  output_file_path: {new_db_file}")
        
        cursor.execute(
            "UPDATE research_sessions SET output_folder = ?, output_file_path = ? WHERE id = ?",
            (new_db_folder, new_db_file, cfg["id"])
        )
        conn.commit()
        print("  Database update: SUCCESS")
    else:
        print(f"Session {cfg['id']} not found in database.")
        
conn.close()
