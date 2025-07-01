import pandas as pd
import streamlit as st
import os
from streamlit import session_state

# === Config ===
MASTER_FILE = "v2_metadata_with_image_url_3.csv"
TAGGED_FILE = "tagged_data_10500.csv"

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
    "earring_type", "stud_subtype", "center_setting", "side_setting", "diameter", "hoop_subtype", "image_url", "tagger"
]

if os.path.exists(TAGGED_FILE) and os.path.getsize(TAGGED_FILE) > 0:
    df_tagged = pd.read_csv(TAGGED_FILE)
else:
    df_tagged = pd.DataFrame(columns=tagged_columns)

import os
from datetime import datetime

def safe_save(df, path="tagged.csv"):
    min_row_threshold = 20  # adjust as needed

    if df.empty or len(df) < min_row_threshold:
        st.error(f"❌ Save aborted: Only {len(df)} rows in memory. Abnormal state detected.")
        return

    # Save backup with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    with open("save_log.txt", "a") as log:
        log.write(f"[{timestamp}] Saved {len(df)} rows → {path}\n")

    backup_path = f"tagging_backups/{os.path.basename(path).replace('.csv', f'_{timestamp}.csv')}"
    os.makedirs("tagging_backups", exist_ok=True)
    df.to_csv(backup_path, index=False)

    # Save main file
    df.to_csv(path, index=False)
    st.success(f"✅ Saved {len(df)} rows to `{path}` + backup.")


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

# === End condition ===
if df_unseen.empty:
    st.success("🎉 All images have been tagged!")
else:
    row = df_unseen[df_unseen["filename"] == st.session_state.current_filename].iloc[0]
    st.image(row["image_url"], width=300)

    
    style_cd = row["style_cd"]
    filename = row["filename"]
    description = row["description"] if "description" in row else "No description available"

    st.write(f"**Current Style Code:** `{style_cd}`")
    st.write(f"**Current Image Description:** {description}")
    st.write(f"**Current Filename:** `{filename}`")
    new_filename = st.text_input("Propose New Filename (optional)", value=filename, key=f"newname_{filename}")

    if st.button("➡️ Fetch New Image", key=f"skip_{filename}"):
        current_idx = df_unseen.index[df_unseen["filename"] == st.session_state.current_filename][0]
        next_idx = (current_idx + 1) % len(df_unseen)

        st.session_state.current_filename = df_unseen.iloc[next_idx]["filename"]
        st.rerun()


    # === Dropdowns ===
    category_view_map = {
        "RING": ["","PRIMARY", "TOP", "FRONT", "TOP-FRONT", "3/4", "SIDE", "BACK", "MODEL", "SCALE"],
        "BRACELET": ["","PRIMARY", "FULL", "CLASP", "O","MODEL", "SCALE"],
        "NECKLACE": ["", "FULL", "PRIMARY", "CLASP", "MODEL", "SCALE"],
        "EARRING": ["", "BACK", "FRONT", "3/4", "TOP", "TOP-3/4", "TOP-SIDE","SIDE", "MODEL", "SCALE", "MODEL-SCALE"],
        "PENDANT": ["", "PRIMARY", "3/4", "SIDE", "BACK", "CLASP", "MODEL", "SCALE"],
        "BANGLE": ["", "PRIMARY", "SIDE", "O" "MODEL", "SCALE"],
        "ANKLET": ["","PRIMARY" "FULL", "CLASP", "O","MODEL", "SCALE"]
    }

    style_category_val = row.get("style_category", "")
    view_options = category_view_map.get(style_category_val, ["", "FRONT", "SIDE", "MODEL", "SCALE"])

    default_view_idx = 0
    if pd.notna(row.get("view")) and row["view"] in view_options:
        default_view_idx = view_options.index(row["view"])

    view = st.selectbox(
        "View",
        view_options,
        index=default_view_idx,
        key=f"view_{filename}"
    )



    style_options = ["", "RING", "BRACELET", "EARRING", "NECKLACE", "PENDANT", "BANGLE", "ANKLET"]
    default_style_idx = 0
    if pd.notna(row["style_category"]) and row["style_category"] in style_options:
        default_style_idx = style_options.index(row["style_category"])

    style_category = st.selectbox(
        "Style Category",
        style_options,
        index=default_style_idx,
        key=f"sc_{filename}"
    )


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
    "Black Rhodium": "BR",
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
        "None", "Unknown", "Constellation", "Zodiac / Horoscope", "Kaleioscope", "Flora", "Sphere", "Align",
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

    center_setting = st.selectbox(
            "Center Setting",
            ["", "6-prong", "5-Prong", "4-prong", "3-prong", "2-prong", "Channel", "Bezel", "Invisible", "Prong", "N/A"],
            key=f"center_setting_{filename}"
        )
    
    side_setting = st.selectbox(
            "Side Setting",
            ["","6-prong", "4-prong", "3-prong", "2-prong", "Prong", "Channel", "Bezel", "Nick", "Invisible", "N/A"],
            key=f"side_setting_{filename}"
        )
    
    
    diamond_shapes = [
    "ROUND", "PRINCESS", "CUSHION", "OVAL", "EMERALD", "PEAR", "HEART", "ASSCHER",
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
        chain_options = ["", "BOX CHAIN", "BEAD CHAIN", "CABLE CHAIN", "CABLE-DC CHAIN", "CUBAN LINK CHAIN", "CURB CHAIN", "HYDRO CHAIN","PAPER CLIP CHAIN", "ROLO CHAIN", "ROPE CHAIN", "ROUND WHEAT CHAIN"]
        default_idx = 0
        if pd.notna(row["chain_type"]) and row["chain_type"] in chain_options:
            default_idx = chain_options.index(row["chain_type"])

        chain_type = st.selectbox(
            "Chain Type",
            chain_options,
            index=default_idx,
            key=f"ct_{filename}"
        )


    gender = st.selectbox("Gender", ["LADIES", "GENTS"],
        index=["LADIES", "GENTS"].index(row["gender"]) if pd.notna(row["gender"]) and row["gender"] in ["LADIES", "GENTS"] else 0,
        key=f"g_{filename}")
    
    

    is_set = st.checkbox("Is Set", value=bool(row["is_set"]), key=f"s_{filename}")

    comments = st.text_area("Comments / Notes", height=80, key=f"comments_{filename}")
    cant_view_image = st.checkbox("⚠️ Image did not render / can’t be viewed", key=f"noview_{filename}")

    # === Save Tag ===
    if st.button("📂 Save", key=f"save_{filename}"):
        # Always reload the latest on-disk file
        if os.path.exists(TAGGED_FILE) and os.path.getsize(TAGGED_FILE) > 0:
            df_tagged = pd.read_csv(TAGGED_FILE)
        else:
            df_tagged = pd.DataFrame(columns=tagged_columns)

        new_row = {
            "filename": filename,
            "original_filename": filename,
            "new_filename": new_filename.strip() if new_filename.strip() != filename else "",
            "image_url": row["image_url"],
            "style_cd": style_cd,
            "view": view,
            "style_category": style_category,
            "cstone_shape": ", ".join(cstone_shapes),
            "ring_type": ring_type if style_category == "RING" else "",
            "chain_type": chain_type if style_category in ["NECKLACE", "PENDANT", "BRACELET"] else "",
            "earring_type": earring_type if style_category == "EARRING" else "",
            "metal_type": metal_type,
            "metal_color": metal_color,
            "center_setting": center_setting,
            "side_setting": side_setting,
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
        df_tagged = df_tagged.drop_duplicates(subset="filename", keep="last")
        safe_save(df_tagged, TAGGED_FILE)

        # Recalculate df_unseen and advance
        tagged_filenames = set(df_tagged["filename"])
        df_unseen = df_master[~df_master["filename"].isin(tagged_filenames)].reset_index(drop=True)

        if not df_unseen.empty:
            st.session_state.current_filename = df_unseen.iloc[0]["filename"]
        else:
            del st.session_state["current_filename"]

        st.rerun()
