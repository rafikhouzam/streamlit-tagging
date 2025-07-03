# utils/recovery.py
import pandas as pd
import os
from datetime import datetime

def auto_recover_csv(main_path, backup_dir, recovery_log="recovery_log.txt", threshold=50):
    def count_rows(path):
        try:
            return pd.read_csv(path).shape[0]
        except:
            return 0

    current_count = count_rows(main_path)

    best_backup = None
    max_rows = -1
    for f in os.listdir(backup_dir):
        if f.endswith(".csv"):
            path = os.path.join(backup_dir, f)
            rows = count_rows(path)
            if rows > max_rows:
                max_rows = rows
                best_backup = path

    if current_count < max_rows - threshold and best_backup:
        os.system(f"cp '{best_backup}' '{main_path}'")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"[{timestamp}] 🔁 Auto-recovered from backup ({current_count} → {max_rows} rows): {best_backup}\n"

        with open(recovery_log, "a") as log:
            log.write(msg)

        try:
            import streamlit as st
            st.warning("⚠️ Auto-recovered from data corruption. Last good backup restored.")
        except:
            pass

        print(msg.strip())

    return pd.read_csv(main_path)
