import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import os

# ===============================
# CONFIG
# ===============================
st.set_page_config(layout="wide")

DATA_PATH = "data.csv"
TIME_PATH = "last_update.txt"
wib = ZoneInfo("Asia/Jakarta")

# ===============================
# LOAD & SAVE GLOBAL DATA
# ===============================
def load_data():
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH)
    return None

def save_data(df):
    df.to_csv(DATA_PATH, index=False)
    with open(TIME_PATH, "w") as f:
        f.write(datetime.now(wib).strftime("%H:%M"))

def get_last_update():
    if os.path.exists(TIME_PATH):
        with open(TIME_PATH, "r") as f:
            return f.read().strip()
    return None

df = load_data()
last_update_time = get_last_update()

# ===============================
# HEADER (TITLE + UPLOAD BUTTON)
# ===============================
col1, col2 = st.columns([6,2])

with col1:
    st.markdown("## 📊 OSS Monitoring Dashboard")

with col2:
    uploaded_files = st.file_uploader(
        "Drag and drop files here",
        type=["csv"],
        accept_multiple_files=True,  # ✅ FIX: multiple file support
        label_visibility="collapsed"
    )

# ===============================
# SAVE DATA IF UPLOADED
# ===============================
if uploaded_files:
    df_list = []

    for file in uploaded_files:
        temp_df = pd.read_csv(file)
        df_list.append(temp_df)

    merged_df = pd.concat(df_list, ignore_index=True)
    save_data(merged_df)

    st.rerun()

# ===============================
# BLINKING UPDATE TEXT
# ===============================
last_update_time = get_last_update()

if last_update_time:
    st.markdown(f"""
        <style>
        @keyframes blink {{
            50% {{ opacity: 0; }}
        }}
        .blink-text {{
            text-align:center;
            font-weight:bold;
            font-size:18px;
            color:white;
            animation: blink 1s linear infinite;
        }}
        </style>
        <div class="blink-text">
            Data Diperbarui pada {last_update_time} WIB
        </div>
    """, unsafe_allow_html=True)

# ===============================
# MENU BAR
# ===============================
st.markdown("""
------------------------------------------------------
| TIKET AKTIF | TIKET CLOSE | DOWNLOAD TIKET |
------------------------------------------------------
""")

# ===============================
# PROCESS DATA IF EXISTS
# ===============================
df = load_data()

if df is not None:

    # ===== FIX TIMEZONE ERROR =====
    if "REPORTED DATE" in df.columns:
        df["REPORTED DATE"] = pd.to_datetime(df["REPORTED DATE"], errors="coerce")
        df["REPORTED DATE"] = df["REPORTED DATE"].dt.tz_localize(None)

        now_naive = datetime.now(wib).replace(tzinfo=None)
        df["UMUR_TIKET_HARI"] = (now_naive - df["REPORTED DATE"]).dt.days

    # ===== FINAL FIELDS =====
    final_columns = [
        "Incident",
        "witel",
        "Layanan",
        "service id",
        "Jenis",
        "Severity",
        "TTR",
        "Customer",
        "last update",
        "worklog",
        "WorkLogs summary"
    ]

    existing_columns = [col for col in final_columns if col in df.columns]
    df_display = df[existing_columns].copy()

    # ===============================
    # COPY BUTTON COLUMN 📑
    # ===============================
    def generate_copy_text(summary):
        return f"mohon dibantu kembali info progres saat ini 🙏\nupdate terakhir : {summary}"

    if "WorkLogs summary" in df_display.columns:
        df_display["📑"] = df_display["WorkLogs summary"].apply(generate_copy_text)
    else:
        df_display["📑"] = ""

    # ===============================
    # DISPLAY TABLE + COPY BUTTON
    # ===============================
    for index, row in df_display.iterrows():
        cols = st.columns(len(existing_columns) + 1)

        for i, col in enumerate(existing_columns):
            cols[i].write(row[col])

        copy_text = row["📑"]
        if cols[-1].button("copy", key=f"copy_{index}"):
            st.code(copy_text)
            st.success("Teks berhasil disalin, tinggal paste ke teknisi 👍")

else:
    st.info("Silakan upload file CSV terlebih dahulu.")
