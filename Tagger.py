import pandas as pd
import streamlit as st
import os
from streamlit import session_state

# === Config ===
MASTER_FILE = "final_image_metadata_with_urls.csv"
TAGGED_FILE = "tagged_data.csv"

# === Load and cache shuffled master data ===
if "df_master" not in st.session_state:
    df_master = pd.read_csv(MASTER_FILE)
    df_master = df_master.sample(frac=1).reset_index(drop=True)
    st.session_state.df_master = df_master
else:
    df_master = st.session_state.df_master

# === Load or initialize tagged data ===
if os.path.exists(TAGGED_FILE) and os.path.getsize(TAGGED_FILE) > 0:
    df_tagged = pd.read_csv(TAGGED_FILE)
else:
    df_tagged = pd.DataFrame(columns=[
        "filename", "style_cd", "style_category", "ring_type", "cstone_shape",
        "chain_type", "metal_color", "gender", "is_set"
    ])


tagged_filenames = set(df_tagged["filename"])
df_unseen = df_master[~df_master["filename"].isin(tagged_filenames)].reset_index(drop=True)

# === Progress bar ===
progress = len(tagged_filenames) / len(df_master)
st.progress(progress)
st.write(f"**Tagged {len(tagged_filenames)} out of {len(df_master)} images ({progress:.1%})**")

# === Initialize session state for current image ===
if "current_filename" not in st.session_state and not df_unseen.empty:
    st.session_state.current_filename = df_unseen.iloc[0]["filename"]

# === End condition ===
if df_unseen.empty:
    st.success("🎉 All images have been tagged!")
else:
    row = df_unseen[df_unseen["filename"] == st.session_state.current_filename].iloc[0]
    st.image(row["full_path"], width=300)

    style_cd = row["style_cd"]
    filename = row["filename"]

    if st.button("➡️ Fetch New Image", key=f"skip_{filename}"):
        current_idx = df_unseen.index[df_unseen["filename"] == st.session_state.current_filename][0]
        next_idx = (current_idx + 1) % len(df_unseen)

        st.session_state.current_filename = df_unseen.iloc[next_idx]["filename"]
        st.rerun()


    # === Dropdowns ===
    style_category = st.selectbox("Style Category", ["", "RING", "BRACELET", "EARRING", "NECKLACE", "PENDANT", "BANGLE", "ANKLET"],
        index=0 if pd.isna(row["style_category"]) else ["", "RING", "BRACELET", "EARRING", "NECKLACE", "PENDANT", "BANGLE", "ANKLET"].index(row["style_category"]),
        key=f"sc_{filename}")

    ring_type = st.selectbox("Ring Type", ["", "BRIDAL", "ENGAGEMENT", "ANNIVERSARY", "FASHION", "GENTS", "WEDDING"],
        index=0 if pd.isna(row["ring_type"]) else ["", "BRIDAL", "ENGAGEMENT", "ANNIVERSARY", "FASHION", "GENTS", "WEDDING"].index(row["ring_type"]) if row["ring_type"] in ["BRIDAL", "ENGAGEMENT", "ANNIVERSARY", "FASHION", "GENTS", "WEDDING"] else 0,
        key=f"rt_{filename}")

    chain_type = st.selectbox("Chain Type", ["", "PAPER CLIP CHAIN", "ROPE CHAIN", "BOX CHAIN", "CUBAN LINK CHAIN", "BEAD CHAIN"],
        index=0 if pd.isna(row["chain_type"]) else ["", "PAPER CLIP CHAIN", "ROPE CHAIN", "BOX CHAIN", "CUBAN LINK CHAIN", "BEAD CHAIN"].index(row["chain_type"]) if row["chain_type"] in ["PAPER CLIP CHAIN", "ROPE CHAIN", "BOX CHAIN", "CUBAN LINK CHAIN", "BEAD CHAIN"] else 0,
        key=f"ct_{filename}")

    metal_color = st.selectbox("Metal Color", ["", "W", "Y", "R", "TT", "TRI"],
        index=0 if pd.isna(row["metal_color"]) else ["", "W", "Y", "R", "TT", "TRI"].index(row["metal_color"]) if row["metal_color"] in ["W", "Y", "R", "TT", "TRI"] else 0,
        key=f"mc_{filename}")

    gender = st.selectbox("Gender", ["LADIES", "GENTS"],
        index=["LADIES", "GENTS"].index(row["gender"]) if pd.notna(row["gender"]) and row["gender"] in ["LADIES", "GENTS"] else 0,
        key=f"g_{filename}")

    is_set = st.checkbox("Is Set", value=bool(row["is_set"]), key=f"s_{filename}")

    # === Save Tag ===
    if st.button("📂 Save", key=f"save_{filename}"):
        new_row = {
            "filename": filename,
            "style_cd": style_cd,
            "style_category": style_category,
            "ring_type": ring_type,
            "chain_type": chain_type,
            "metal_color": metal_color,
            "gender": gender,
            "is_set": is_set
        }

        df_tagged = pd.concat([df_tagged, pd.DataFrame([new_row])], ignore_index=True)
        df_tagged.to_csv(TAGGED_FILE, index=False)

        # Recalculate df_unseen and advance
        tagged_filenames = set(df_tagged["filename"])
        df_unseen = df_master[~df_master["filename"].isin(tagged_filenames)].reset_index(drop=True)

        if not df_unseen.empty:
            st.session_state.current_filename = df_unseen.iloc[0]["filename"]
        else:
            del st.session_state["current_filename"]

        st.rerun()
