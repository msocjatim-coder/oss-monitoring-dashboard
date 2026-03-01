import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="OSS Monitoring Dashboard", layout="wide")

DATA_FILE = "oss_data_shared.csv"

st.title("📊 OSS Monitoring Dashboard")

# ================= MENU BAR =================
tab1, tab2, tab3 = st.tabs(
    ["TIKET AKTIF", "TIKET CLOSE", "DOWNLOAD TIKET"]
)

# ================= UPLOAD (HANYA SEKALI) =================
with st.expander("Upload Semua File CSV dari OSS (Upload jika ada update data)"):
    uploaded_files = st.file_uploader(
        "Upload CSV (Bisa banyak sekaligus)",
        type=["csv"],
        accept_multiple_files=True
    )

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

        df = pd.concat(df_list, ignore_index=True)

        df.to_csv(DATA_FILE, index=False)

        st.success("Data berhasil disimpan & dapat diakses semua user.")

# ================= LOAD DATA UNTUK SEMUA USER =================
if not os.path.exists(DATA_FILE):
    st.warning("Belum ada data. Silakan upload terlebih dahulu.")
    st.stop()

df = pd.read_csv(DATA_FILE)

# ================= VALIDASI KOLOM DASAR =================
required_columns = ["INCIDENT", "STATUS", "WITEL", "REPORTED DATE", "SUMMARY"]
missing_cols = [col for col in required_columns if col not in df.columns]

if missing_cols:
    st.error(f"Kolom berikut tidak ditemukan: {missing_cols}")
    st.stop()

# ================= PROCESSING (TIDAK DIUBAH) =================
df = df.drop_duplicates(subset=["INCIDENT"])

df["REPORTED DATE"] = pd.to_datetime(df["REPORTED DATE"], errors="coerce")
df["UMUR_TIKET_HARI"] = (datetime.now() - df["REPORTED DATE"]).dt.days

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

df["JENIS_GANGGUAN"] = df["SUMMARY"].apply(detect_jenis)

severity_list = ["PREMIUM", "CRITICAL", "MAJOR", "MINOR", "LOW"]

def detect_severity(summary):
    summary = summary.upper()
    for sev in severity_list:
        if sev in summary:
            return sev
    return "-"

df["SEVERITY"] = df["SUMMARY"].apply(detect_severity)

# ================= FORMAT TAMBAHAN =================

if "TTR CUSTOMER" in df.columns:
    def format_ttr(ttr_value):
        try:
            time_obj = pd.to_datetime(ttr_value, format="%H:%M:%S")
            hours = time_obj.hour
            minutes = time_obj.minute
            return f"{hours} jam {minutes} menit"
        except:
            return ttr_value

    df["TTR CUSTOMER"] = df["TTR CUSTOMER"].apply(format_ttr)

if "LAST UPDATE WORKLOG" in df.columns:
    df["LAST UPDATE WORKLOG"] = pd.to_datetime(
        df["LAST UPDATE WORKLOG"], errors="coerce"
    ).dt.strftime("%H:%M:%S")

# ============================================================
# ===================== TAB 1 : TIKET AKTIF ==================
# ============================================================

with tab1:

    st.subheader("📋 Data Monitoring Tiket Aktif")

    df_active = df[df["IS_ACTIVE"] == True].copy()

    df_display = df_active[
        [
            "INCIDENT",
            "WITEL",
            "LAYANAN",
            "SERVICE ID",
            "JENIS_GANGGUAN",
            "SEVERITY",
            "TTR CUSTOMER",
            "LAST UPDATE WORKLOG",
            "WORKLOG SUMMARY",
        ]
    ].copy()

    df_display.index = range(1, len(df_display) + 1)

    def highlight_severity_column(val):
        color_map = {
            "PREMIUM": "background-color: #800000; color: white;",
            "CRITICAL": "background-color: red; color: white;",
            "MAJOR": "background-color: orange;",
            "MINOR": "background-color: yellow;",
            "LOW": "background-color: lightgreen;",
        }
        return color_map.get(val, "")

    styled_df = df_display.style.applymap(
        highlight_severity_column,
        subset=["SEVERITY"]
    )

    st.dataframe(styled_df, use_container_width=True)

# ============================================================
# ===================== TAB 2 : TIKET CLOSE ==================
# ============================================================

with tab2:

    st.subheader("📁 Data Tiket Close")

    df_close = df[df["IS_ACTIVE"] == False].copy()

    # Pastikan kolom CLOSE ada
    if "CLOSE" not in df_close.columns:
        df_close["CLOSE"] = "-"

    df_close["CLOSE"] = df_close["CLOSE"].fillna("-")

    # Jika kolom SALSIM tidak ada
    if "SALSIM" not in df_close.columns:
        df_close["SALSIM"] = "-"

    df_close_display = df_close[
        [
            "INCIDENT",
            "WITEL",
            "SUMMARY",
            "REPORTED DATE",
            "SALSIM",
            "CLOSE",
        ]
    ].copy()

    df_close_display.index = range(1, len(df_close_display) + 1)

    st.dataframe(df_close_display, use_container_width=True)

# ============================================================
# ===================== TAB 3 : DOWNLOAD =====================
# ============================================================

with tab3:

    st.subheader("⬇ Download Semua Data")

    csv_download = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Semua Data (CSV)",
        data=csv_download,
        file_name="oss_full_data.csv",
        mime="text/csv"
    )
