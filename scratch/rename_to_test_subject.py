import os
import sqlite3
import shutil

db_path = "scout_results.db"
outputs_dir = r"c:\Users\yasha\Desktop\scout\outputs"
old_name = "difference_in_3pl_and_payment_gateways_who_provides_what_how_20260604024411_aa450cdf"
new_name = "test_subject"
session_id = "aa450cdf"

old_path = os.path.join(outputs_dir, old_name)
new_path = os.path.join(outputs_dir, new_name)

print("Starting renaming process...")

# 1. Rename folder on disk
if os.path.exists(old_path):
    print(f"Renaming folder on disk:\n  From: {old_path}\n  To:   {new_path}")
    if os.path.exists(new_path):
        print(f"Target folder {new_path} already exists. Removing it first.")
        shutil.rmtree(new_path)
    shutil.move(old_path, new_path)
    print("Disk rename: SUCCESS")
else:
    print(f"Folder not found or already renamed: {old_path}")

# 2. Update SQLite database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT output_folder, output_file_path FROM research_sessions WHERE id = ?", (session_id,))
row = cursor.fetchone()
if row:
    db_folder, db_file = row
    new_db_folder = os.path.join(outputs_dir, new_name)
    new_db_file = None
    if db_file:
        # Replace the old folder name with the new folder name in the report path
        new_db_file = db_file.replace(old_name, new_name)
        
    print(f"Updating database for session {session_id}:")
    print(f"  output_folder: {new_db_folder}")
    print(f"  output_file_path: {new_db_file}")
    
    cursor.execute(
        "UPDATE research_sessions SET output_folder = ?, output_file_path = ? WHERE id = ?",
        (new_db_folder, new_db_file, session_id)
    )
    conn.commit()
    print("Database update: SUCCESS")
else:
    print(f"Session {session_id} not found in database.")

conn.close()
print("Done!")
