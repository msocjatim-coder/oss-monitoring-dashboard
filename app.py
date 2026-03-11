import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="OSS Monitoring Dashboard", layout="wide")

# ============================================================
# AUTO REFRESH (30 MENIT)
# ============================================================

st_autorefresh = st.experimental_rerun

# ============================================================
# GOOGLE SHEET CONFIG
# ============================================================

SHEET_NAME = "OSS Incident Insera"

wib = ZoneInfo("Asia/Jakarta")

# ============================================================
# GOOGLE SHEET CONNECTION (STREAMLIT CLOUD VERSION)
# ============================================================

def connect_google_sheet():

    creds_dict = st.secrets["gcp_service_account"]

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_dict,
        scope
    )

    client = gspread.authorize(creds)

    sheet = client.open(SHEET_NAME).sheet1

    return sheet

# ============================================================
# HEADER
# ============================================================

col1, col2 = st.columns([8,2])

with col1:
    st.title("📊 OSS Monitoring Dashboard")

with col2:

    uploaded_files = st.file_uploader(
        "",
        type=["csv"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

# ============================================================
# HANDLE UPLOAD
# ============================================================

if uploaded_files:

    df_list = []

    for uploaded_file in uploaded_files:

        df_temp = pd.read_csv(
            uploaded_file,
            low_memory=False,
            on_bad_lines="skip"
        )

        df_temp.columns = (
            df_temp.columns
            .str.strip()
            .str.replace('"', '', regex=False)
            .str.replace(',', '', regex=False)
        )

        df_list.append(df_temp)

    df = pd.concat(df_list, ignore_index=True)

    sheet = connect_google_sheet()

    sheet.clear()

    sheet.update(
        [df.columns.values.tolist()] +
        df.fillna("").values.tolist()
    )

    st.success("Data berhasil disimpan ke Google Sheet")

# ============================================================
# LOAD DATA DARI GOOGLE SHEET
# ============================================================

sheet = connect_google_sheet()

data = sheet.get_all_records()

if len(data) == 0:

    st.warning("Belum ada data. Silakan upload CSV terlebih dahulu.")
    st.stop()

df = pd.DataFrame(data)

# ============================================================
# JAM UPDATE
# ============================================================

now_time = datetime.now(wib).strftime("%H:%M")

st.markdown(
    f"### Data terakhir diperbarui sekitar {now_time} WIB"
)

st.markdown("---")

# ============================================================
# VALIDASI KOLOM
# ============================================================

required_columns = ["INCIDENT","STATUS","WITEL","REPORTED DATE","SUMMARY"]

missing_cols = [col for col in required_columns if col not in df.columns]

if missing_cols:

    st.error(f"Kolom berikut tidak ditemukan: {missing_cols}")
    st.stop()

# ============================================================
# PROCESSING
# ============================================================

df = df.drop_duplicates(subset=["INCIDENT"])

df["REPORTED DATE"] = pd.to_datetime(
    df["REPORTED DATE"],
    errors="coerce"
)

now = datetime.now(wib).replace(tzinfo=None)

df["UMUR_TIKET_HARI"] = (
    now - df["REPORTED DATE"]
).dt.days

df["IS_ACTIVE"] = ~df["STATUS"].astype(str).str.lower().isin(
    ["closed","resolved","cancel"]
)

df["LAYANAN"] = df["SUMMARY"].apply(
    lambda x: "TSEL" if "TSEL" in str(x).upper() else "OLO"
)

# ============================================================
# TAB DASHBOARD
# ============================================================

tab1, tab2, tab3 = st.tabs(
    ["TIKET AKTIF","TIKET CLOSE","DOWNLOAD"]
)

with tab1:

    df_active = df[df["IS_ACTIVE"] == True]

    st.dataframe(df_active, use_container_width=True)

with tab2:

    st.dataframe(df, use_container_width=True)

with tab3:

    csv_download = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Semua Data",
        data=csv_download,
        file_name="oss_full_data.csv",
        mime="text/csv"
    )
