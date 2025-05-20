import pandas as pd
import streamlit as st
import os
from streamlit import session_state

# === Config ===
MASTER_FILE = "final_metadata_streamlit_ready.csv"
TAGGED_FILE = "tagged_data_2.csv"

# === Tagger credentials (name: pin) ===
TAGGERS = dict(st.secrets["taggers"])

# === Auth ===
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    name = st.text_input("Your Name")
    pin = st.text_input("4-digit PIN", type="password")

    if name in TAGGERS and pin == TAGGERS[name]:
        st.session_state.authenticated = True
        st.session_state.tagger = name
        st.rerun()
    elif name and pin:
        st.error("Invalid name or PIN")
    st.stop()

# === Load and cache shuffled master data ===
if "df_master" not in st.session_state:
    df_master = pd.read_csv(MASTER_FILE)
    df_master = df_master.sample(frac=1).reset_index(drop=True)
    st.session_state.df_master = df_master
else:
    df_master = st.session_state.df_master

# === Load or initialize tagged data ===
tagged_columns = [
    "filename", "original_filename", "new_filename", "style_cd", "style_category", "ring_type", "cstone_shape",
    "chain_type", "metal_color", "metal_type", "gender", "collection", "is_set",
    "earring_type", "stud_subtype", "setting", "diameter", "hoop_subtype", "image_url"
]

if os.path.exists(TAGGED_FILE) and os.path.getsize(TAGGED_FILE) > 0:
    df_tagged = pd.read_csv(TAGGED_FILE)
else:
    df_tagged = pd.DataFrame(columns=tagged_columns)

df_master["filename"] = df_master["image_url"].apply(lambda x: os.path.basename(str(x)))
tagged_filenames = set(df_tagged["original_filename"])
df_unseen = df_master[~df_master["filename"].isin(tagged_filenames)].reset_index(drop=True)

# === Progress bar ===
progress = len(tagged_filenames) / len(df_master)
st.progress(progress)
st.write(f"**Tagged {len(tagged_filenames)} out of {len(df_master)} images ({progress:.1%})**")

# Safe defaults in case the user is not tagging earrings
earring_type = ""
stud_subtype = ""
setting = ""
diameter = ""
hoop_subtype = ""

# === Initialize session state for current image ===
if "current_filename" not in st.session_state and not df_unseen.empty:
    st.session_state.current_filename = df_unseen.iloc[0]["filename"]

# === Leaderboard Sidebar ===
st.sidebar.markdown("### 👥 Leaderboard")
if not df_tagged.empty:
    leaderboard = df_tagged["tagger"].value_counts().reset_index()
    leaderboard.columns = ["Tagger", "Tags"]
else:
    # Show all taggers with 0 by default
    leaderboard = pd.DataFrame({
        "Tagger": list(TAGGERS.keys()),
        "Tags": [0] * len(TAGGERS)
    })

st.sidebar.dataframe(leaderboard)

# === End condition ===
if df_unseen.empty:
    st.success("🎉 All images have been tagged!")
else:
    row = df_unseen[df_unseen["filename"] == st.session_state.current_filename].iloc[0]
    st.image(row["image_url"], width=300)

    
    style_cd = row["style_cd"]
    filename = row["filename"]

    st.write(f"**Current Style Code:** `{style_cd}`")
    st.write(f"**Current Filename:** `{filename}`")
    new_filename = st.text_input("Propose New Filename (optional)", value=filename, key=f"newname_{filename}")

    if st.button("➡️ Fetch New Image", key=f"skip_{filename}"):
        current_idx = df_unseen.index[df_unseen["filename"] == st.session_state.current_filename][0]
        next_idx = (current_idx + 1) % len(df_unseen)

        st.session_state.current_filename = df_unseen.iloc[next_idx]["filename"]
        st.rerun()


    # === Dropdowns ===
    style_category = st.selectbox("Style Category", ["", "RING", "BRACELET", "EARRING", "NECKLACE", "PENDANT", "BANGLE", "ANKLET"],
        index=0 if pd.isna(row["style_category"]) else ["", "RING", "BRACELET", "EARRING", "NECKLACE", "PENDANT", "BANGLE", "ANKLET"].index(row["style_category"]),
        key=f"sc_{filename}")

    # === Metal Type ===
    metal_type = st.selectbox(
        "Metal Type",
        ["", "10KT", "14KT", "18KT", "22KT", "PLAT", "PT", "SILV", "STER", "BRAS", "GOSI", "PALD", "9KT", "RP"],
        index=0 if pd.isna(row.get("metal_typ")) else ["", "10KT", "14KT", "18KT", "22KT", "PLAT", "PT", "SILV", "STER", "BRAS", "GOSI", "PALD", "9KT", "RP"].index(row["metal_typ"]) if row["metal_typ"] in ["10KT", "14KT", "18KT", "22KT", "PLAT", "PT", "SILV", "STER", "BRAS", "GOSI", "PALD", "9KT", "RP"] else 0,
        key=f"mt_{filename}"
    )

    # === Metal Color (Display full name, save suffix) ===
    metal_color_map = {
    "White": "W",
    "Yellow": "Y",
    "Yellow Vermeil": "YV",
    "Pink": "P",
    "Pink Vermeil": "PV",
    "Pink White": "PW",
    "Rose Gold": "R",
    "Two Tone": "T",
    "Tri Color": "3",
    "G": "G",
    "N": "N"
    }

    metal_color_display = st.selectbox(
        "Metal Color",
        [""] + list(metal_color_map.keys()),
        key=f"mc_{filename}"
    )

    metal_color = metal_color_map.get(metal_color_display, "")


    # === Collection ===
    collections = [
        "None", "Constellation", "Zodiac / Horoscope", "Kaleioscope", "Flora", "Sphere", "Align",
        "4 Stone Marquise", "Trinity Heart", "Tulip", "Spark of Love", "Dandelion", "Sinfonia",
        "Everlasting Love", "Love Bloom", "Where you belong…in my heart", "Petals of Love",
        "Angel Numbers", "Overlay", "Journey of you", "Celebration", "Unlock", "Mother and Child",
        "Paperclip", "Fleur De Lis", "Waterfall", "Show your smile", "Dawn", "Love we share",
        "Liora", "Hugs & Kisses (XOXO)"
    ]

    collection = st.selectbox(
        "Collection",
        collections,
        index=0 if pd.isna(row.get("collection")) else collections.index(row["collection"]) if row["collection"] in collections else 0,
        key=f"coll_{filename}"
    )

    
    if style_category == "EARRING":
        earring_type = st.selectbox(
            "Earring Type",
            ["", "Stud", "Hoop", "Fashion"],
            key=f"et_{filename}"
        )

    # === Stud branch
    if earring_type == "Stud":
        stud_subtype = st.selectbox(
            "Stud Subtype",
            ["", "Cluster", "Solitaire", "Other"],
            key=f"studtype_{filename}"
        )

       

    # === Hoop branch
    elif earring_type == "Hoop":
        diameter = st.select_slider(
            "Hoop Diameter (inches)",
            options=[round(x * 0.25, 2) for x in range(2, 9)],  # 0.5 to 2.0
            key=f"diameter_{filename}"
        )

        hoop_subtype = st.selectbox(
            "Hoop Subtype",
            ["", "Huggie", "Inside Out", "Outside Only"],
            key=f"hoopsub_{filename}"
        )

        # Optional: Smart assist for auto-classifying Huggie
        if diameter <= 0.5 and hoop_subtype == "":
            st.info("This may qualify as a Huggie due to small diameter.")


    # === Fashion branch (currently no subfields)
    elif earring_type == "Fashion":
        st.write("No additional details for Fashion earrings (yet!)")

    setting = st.selectbox(
            "Setting",
            ["6-prong", "4-prong", "3-prong", "2-prong", "Bezel", "Invisible", "N/A"],
            key=f"setting_{filename}"
        )
    
    diamond_shapes = [
    "ROUND", "PRINCESS", "CUSHION", "OVAL", "EMERALD", "PEAR", "ASSCHER",
    "KITE", "RADIANT", "MARQUISE", "ELONGATED CUSHION", "HALF MOON",
    "TRILLIANT", "TAPERED BAGUETTE", "BAGUETTE"
    ]

    cstone_shapes = st.multiselect(
    "Center Stone Shape(s)",
    options=diamond_shapes,
    default=[row["cstone_shape"]] if pd.notna(row.get("cstone_shape")) and row["cstone_shape"] in diamond_shapes else [],
    key=f"css_{filename}"
)

    if style_category == "RING":
        ring_type = st.selectbox("Ring Type", ["", "BRIDAL", "ENGAGEMENT", "ANNIVERSARY", "FASHION", "GENTS", "WEDDING"],
            index=0 if pd.isna(row["ring_type"]) else ["", "BRIDAL", "ENGAGEMENT", "ANNIVERSARY", "FASHION", "GENTS", "WEDDING"].index(row["ring_type"]) if row["ring_type"] in ["BRIDAL", "ENGAGEMENT", "ANNIVERSARY", "FASHION", "GENTS", "WEDDING"] else 0,
            key=f"rt_{filename}")
        
    if style_category == "NECKLACE" or style_category == "PENDANT" or style_category == "BRACELET":
        chain_type = st.selectbox("Chain Type", ["", "PAPER CLIP CHAIN", "ROPE CHAIN", "BOX CHAIN", "CUBAN LINK CHAIN", "BEAD CHAIN"],
            index=0 if pd.isna(row["chain_type"]) else ["", "PAPER CLIP CHAIN", "ROPE CHAIN", "BOX CHAIN", "CUBAN LINK CHAIN", "BEAD CHAIN"].index(row["chain_type"]) if row["chain_type"] in ["PAPER CLIP CHAIN", "ROPE CHAIN", "BOX CHAIN", "CUBAN LINK CHAIN", "BEAD CHAIN"] else 0,
            key=f"ct_{filename}")

    gender = st.selectbox("Gender", ["LADIES", "GENTS"],
        index=["LADIES", "GENTS"].index(row["gender"]) if pd.notna(row["gender"]) and row["gender"] in ["LADIES", "GENTS"] else 0,
        key=f"g_{filename}")
    
    

    is_set = st.checkbox("Is Set", value=bool(row["is_set"]), key=f"s_{filename}")

    comments = st.text_area("Comments / Notes", height=80, key=f"comments_{filename}")
    cant_view_image = st.checkbox("⚠️ Image did not render / can’t be viewed", key=f"noview_{filename}")

    # === Save Tag ===
    if st.button("📂 Save", key=f"save_{filename}"):
        new_row = {
            "filename": filename,
            "original_filename": filename,
            "new_filename": new_filename.strip() if new_filename.strip() != filename else "",
            "image_url": row["image_url"],
            "style_cd": style_cd,
            "style_category": style_category,
            "cstone_shape": ", ".join(cstone_shapes),
            "ring_type": ring_type if style_category == "RING" else "",
            "chain_type": chain_type if style_category in ["NECKLACE", "PENDANT", "BRACELET"] else "",
            "earring_type": earring_type if style_category == "EARRING" else "",
            "metal_type": metal_type,
            "metal_color": metal_color,
            "collection": collection,
            "gender": gender,
            "is_set": is_set,
            "stud_subtype": stud_subtype if earring_type == "Stud" else "",
            "diameter": diameter if earring_type == "Hoop" else "",
            "hoop_subtype": hoop_subtype if earring_type == "Hoop" else "",
            "comments": comments,
            "cant_view_image": cant_view_image
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
