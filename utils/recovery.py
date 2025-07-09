import pandas as pd
import os
from datetime import datetime

def auto_recover_csv(main_path, backup_dir, recovery_log="recovery_log.txt", threshold=50, scan_limit=5):
    def count_rows(path):
        try:
            return pd.read_csv(path).shape[0]
        except:
            return 0

    # Step 1: Count rows in current main file
    current_count = count_rows(main_path)

    # Step 2: Get up to `scan_limit` most recent backups
    backup_files = sorted(
        [
            os.path.join(backup_dir, f)
            for f in os.listdir(backup_dir)
            if f.endswith(".csv")
        ],
        key=os.path.getmtime,
        reverse=True
    )[:scan_limit]

    # Step 3: Find the largest valid backup
    best_backup = None
    max_rows = -1

    for path in backup_files:
        rows = count_rows(path)
        if rows > max_rows:
            max_rows = rows
            best_backup = path

    # Step 4: Recover if current is too small
    if current_count < max_rows - threshold and best_backup:
        os.system(f"cp '{best_backup}' '{main_path}'")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"[{timestamp}] 🔁 Auto-recovered from backup ({current_count} → {max_rows} rows): {best_backup}\n"

        # Log to file
        with open(recovery_log, "a") as log:
            log.write(msg)

        # Optional Streamlit UI alert
        try:
            import streamlit as st
            st.warning("⚠️ Auto-recovered from data corruption. Last good backup restored.")
        except:
            pass

        print(msg.strip())

    # Step 5: Return loaded DataFrame
    return pd.read_csv(main_path)
