import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="OSS Monitoring Dashboard", layout="wide")

DATA_FILE = "data_latest.csv"
TIME_FILE = "last_update.txt"

# ============================================================
# ======================= CUSTOM CSS =========================
# ============================================================

st.markdown("""
<style>
[data-testid="stFileUploader"] {
    max-width: 260px !important;
}
[data-testid="stFileUploader"] section {
    padding: 8px 12px 8px 12px !important;
}
[data-testid="stFileUploader"] div[role="button"] {
    min-height: 60px !important;
}
[data-testid="stFileUploader"] small {
    font-size: 12px !important;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# ======================= HEADER =============================
# ============================================================

header_col1, header_col2 = st.columns([9, 1])

with header_col1:
    st.markdown("## 📊 OSS Monitoring Dashboard")

with header_col2:
    uploaded_files = st.file_uploader(
        "",
        type=["csv"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

# ============================================================
# ======================= HANDLE UPLOAD ======================
# ============================================================

if uploaded_files:

    df_list = []

    for uploaded_file in uploaded_files:
        try:
            df_temp = pd.read_csv(uploaded_file)
        except:
            df_temp = pd.read_csv(uploaded_file, encoding="latin1")

        df_temp.columns = df_temp.columns.str.strip()
        df_temp.columns = df_temp.columns.str.replace('"', '', regex=False)
        df_temp.columns = df_temp.columns.str.replace(',', '', regex=False)

        df_list.append(df_temp)

    df_uploaded = pd.concat(df_list, ignore_index=True)

    df_uploaded.to_csv(DATA_FILE, index=False)

    now_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    with open(TIME_FILE, "w") as f:
        f.write(now_time)

st.markdown("---")

# ============================================================
# ======================= LOAD DATA ==========================
# ============================================================

if not os.path.exists(DATA_FILE):
    st.warning("Silakan upload file CSV terlebih dahulu.")
    st.stop()

df = pd.read_csv(DATA_FILE)

# ============================================================
# ======================= VALIDASI KOLOM =====================
# ============================================================

required_columns = [
    "INCIDENT",
    "WITEL",
    "SERVICE ID",
    "SUMMARY",
    "STATUS",
    "REPORTED DATE",
    "CUSTOMER",
    "LAST UPDATE",
    "WORKLOG",
    "WORKLOGS SUMMARY"
]

missing_cols = [col for col in required_columns if col not in df.columns]

if missing_cols:
    st.error(f"Kolom berikut tidak ditemukan: {missing_cols}")
    st.stop()

# ============================================================
# ======================= PROCESSING =========================
# ============================================================

df = df.drop_duplicates(subset=["INCIDENT"])

df["REPORTED DATE"] = pd.to_datetime(df["REPORTED DATE"], errors="coerce")
df["LAST UPDATE"] = pd.to_datetime(df["LAST UPDATE"], errors="coerce")

# TTR dalam jam
df["TTR"] = (df["LAST UPDATE"] - df["REPORTED DATE"]).dt.total_seconds() / 3600
df["TTR"] = df["TTR"].round(2)

df["IS_ACTIVE"] = ~df["STATUS"].str.lower().isin(
    ["closed", "resolved", "cancel"]
)

df["SUMMARY"] = df["SUMMARY"].astype(str)

df["LAYANAN"] = df["SUMMARY"].apply(
    lambda x: "TSEL" if "TSEL" in x.upper() else "OLO"
)

def detect_jenis(summary):
    summary = summary.upper()
    if "RADIOIP" in summary:
        return "RADIOIP"
    elif "TOPOLO" in summary:
        return "TOPOLO"
    elif "METRO" in summary:
        return "METRO"
    elif "CNQ" in summary:
        return "CNQ"
    elif "SLD" in summary:
        return "SLD"
    else:
        return "-"

df["JENIS"] = df["SUMMARY"].apply(detect_jenis)

severity_list = ["PREMIUM", "CRITICAL", "MAJOR", "MINOR", "LOW"]

def detect_severity(summary):
    summary = summary.upper()
    for sev in severity_list:
        if sev in summary:
            return sev
    return "-"

df["SEVERITY"] = df["SUMMARY"].apply(detect_severity)

# ============================================================
# ======================= TABS ===============================
# ============================================================

tab1, tab2, tab3 = st.tabs(["TIKET AKTIF", "TIKET CLOSE", "DOWNLOAD TIKET"])

with tab1:

    df_active = df[df["IS_ACTIVE"] == True].copy()

    st.subheader("📋 Monitoring Dashboard")

    df_display = df_active[
        [
            "INCIDENT",
            "WITEL",
            "LAYANAN",
            "SERVICE ID",
            "JENIS",
            "SEVERITY",
            "TTR",
            "CUSTOMER",
            "LAST UPDATE",
            "WORKLOG",
            "WORKLOGS SUMMARY",
            "SUMMARY"
        ]
    ].copy()

    df_display.index = range(1, len(df_display) + 1)

    st.dataframe(df_display, use_container_width=True)

with tab2:

    df_close = df[df["IS_ACTIVE"] == False].copy()

    st.subheader("📁 Data Tiket Close")

    df_close_display = df_close[
        [
            "INCIDENT",
            "WITEL",
            "LAYANAN",
            "SERVICE ID",
            "JENIS",
            "SEVERITY",
            "TTR",
            "CUSTOMER",
            "LAST UPDATE",
            "WORKLOG",
            "WORKLOGS SUMMARY",
            "SUMMARY"
        ]
    ].copy()

    df_close_display.index = range(1, len(df_close_display) + 1)

    st.dataframe(df_close_display, use_container_width=True)

with tab3:

    st.subheader("⬇ Download Semua Data OSS")

    csv_download = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Semua Data (CSV)",
        data=csv_download,
        file_name="oss_all_ticket.csv",
        mime="text/csv"
    )
