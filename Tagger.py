import pandas as pd
import streamlit as st
import os

# === Config ===
MASTER_FILE = "final_image_metadata.csv"
TAGGED_FILE = "tagged_data.csv"

# === Load master metadata ===
df_master = pd.read_csv(MASTER_FILE)
df_master = df_master.sample(frac=1).reset_index(drop=True)  # shuffle for randomization

# === Load or initialize tagged data ===
if os.path.exists(TAGGED_FILE):
    df_tagged = pd.read_csv(TAGGED_FILE)
    tagged_filenames = set(df_tagged["filename"])
else:
    df_tagged = pd.DataFrame()
    tagged_filenames = set()

# === Progress bar ===
progress = len(tagged_filenames) / len(df_master)
st.progress(progress)
st.write(f"**Tagged {len(tagged_filenames)} out of {len(df_master)} images ({progress:.1%})**")

# === Find next untagged image ===
df_unseen = df_master[~df_master["filename"].isin(tagged_filenames)]

if df_unseen.empty:
    st.success("🎉 All images have been tagged!")
else:
    row = df_unseen.iloc[0]
    st.image(row["full_path"], width=300)

    style_cd = row["style_cd"]
    filename = row["filename"]

    # Dropdowns with default selections
    style_category = st.selectbox(
        "Style Category",
        ["", "RING", "BRACELET", "EARRING", "NECKLACE", "PENDANT", "BANGLE", "ANKLET"],
        index=0 if pd.isna(row["style_category"]) else ["", "RING", "BRACELET", "EARRING", "NECKLACE", "PENDANT", "BANGLE", "ANKLET"].index(row["style_category"]),
        key=f"sc_{filename}"
    )

    ring_type = st.selectbox(
        "Ring Type",
        ["", "BRIDAL", "ENGAGEMENT", "ANNIVERSARY", "FASHION", "GENTS", "WEDDING"],
        index=0 if pd.isna(row["ring_type"]) else ["", "BRIDAL", "ENGAGEMENT", "ANNIVERSARY", "FASHION", "GENTS", "WEDDING"].index(row["ring_type"]) if row["ring_type"] in ["BRIDAL", "ENGAGEMENT", "ANNIVERSARY", "FASHION", "GENTS", "WEDDING"] else 0,
        key=f"rt_{filename}"
    )

    chain_type = st.selectbox(
        "Chain Type",
        ["", "PAPER CLIP CHAIN", "ROPE CHAIN", "BOX CHAIN", "CUBAN LINK CHAIN", "BEAD CHAIN"],
        index=0 if pd.isna(row["chain_type"]) else ["", "PAPER CLIP CHAIN", "ROPE CHAIN", "BOX CHAIN", "CUBAN LINK CHAIN", "BEAD CHAIN"].index(row["chain_type"]) if row["chain_type"] in ["PAPER CLIP CHAIN", "ROPE CHAIN", "BOX CHAIN", "CUBAN LINK CHAIN", "BEAD CHAIN"] else 0,
        key=f"ct_{filename}"
    )

    metal_color = st.selectbox(
        "Metal Color",
        ["", "W", "Y", "R", "TT", "TRI"],
        index=0 if pd.isna(row["metal_color"]) else ["", "W", "Y", "R", "TT", "TRI"].index(row["metal_color"]) if row["metal_color"] in ["W", "Y", "R", "TT", "TRI"] else 0,
        key=f"mc_{filename}"
    )

    gender = st.selectbox(
        "Gender",
        ["LADIES", "GENTS"],
        index=["LADIES", "GENTS"].index(row["gender"]) if pd.notna(row["gender"]) and row["gender"] in ["LADIES", "GENTS"] else 0,
        key=f"g_{filename}"
    )

    is_set = st.checkbox("Is Set", value=bool(row["is_set"]), key=f"s_{filename}")

    if st.button("💾 Save", key=f"save_{filename}"):
        # Store selected values
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
        st.experimental_rerun()
