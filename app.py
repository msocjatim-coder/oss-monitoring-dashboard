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

/* ==== UBAH FILE UPLOADER JADI PERSEGI PANJANG ==== */

[data-testid="stFileUploader"] {
    width: 170px !important;
}

[data-testid="stFileUploader"] section {
    border: none !important;
    padding: 0 !important;
    background: transparent !important;
}

/* HILANGKAN TEKS DRAG & DROP */
[data-testid="stFileUploader"] small {
    display: none !important;
}

[data-testid="stFileUploader"] span {
    display: none !important;
}

/* STYLE TOMBOL */
[data-testid="stFileUploader"] button {
    width: 170px !important;
    height: 42px !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# ======================= HEADER ==============================
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

# ============================================================
# ======================= STATUS BAR =========================
# ============================================================

current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

status_col1, status_col2 = st.columns([6, 4])

with status_col1:
    st.markdown(
        f"""
        <div style='font-size:14px;'>
        🕒 Waktu Sekarang: <b>{current_time} WIB</b>
        </div>
        """,
        unsafe_allow_html=True
    )

if os.path.exists(DATA_FILE) and os.path.exists(TIME_FILE):

    with open(TIME_FILE, "r") as f:
        last_update_time = f.read()

    with status_col2:
        st.markdown(
            f"""
            <div style='text-align:right; font-size:14px;'>
            ✅ Data terakhir diperbarui: <b>{last_update_time} WIB</b>
            </div>
            """,
            unsafe_allow_html=True
        )
else:
    with status_col2:
        st.markdown(
            """
            <div style='text-align:right; font-size:14px; color:red;'>
            ⚠ Belum ada data diupload
            </div>
            """,
            unsafe_allow_html=True
        )

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

required_columns = ["INCIDENT", "STATUS", "WITEL", "REPORTED DATE", "SUMMARY"]
missing_cols = [col for col in required_columns if col not in df.columns]

if missing_cols:
    st.error(f"Kolom berikut tidak ditemukan: {missing_cols}")
    st.stop()

# ============================================================
# ======================= PROCESSING =========================
# ============================================================

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

# ============================================================
# ======================= TABS ===============================
# ============================================================

tab1, tab2, tab3 = st.tabs(["TIKET AKTIF", "TIKET CLOSE", "DOWNLOAD TIKET"])

with tab1:

    df_active = df[df["IS_ACTIVE"] == True].copy()

    st.subheader("📊 Ringkasan")

    total_tiket = len(df_active)
    df_tsel = df_active[df_active["LAYANAN"] == "TSEL"]

    summary_data = {
        "Total Tiket": total_tiket,
        "LOW": len(df_tsel[df_tsel["SEVERITY"] == "LOW"]),
        "MINOR": len(df_tsel[df_tsel["SEVERITY"] == "MINOR"]),
        "MAJOR": len(df_tsel[df_tsel["SEVERITY"] == "MAJOR"]),
        "CRITICAL": len(df_tsel[df_tsel["SEVERITY"] == "CRITICAL"]),
        "PREMIUM": len(df_tsel[df_tsel["SEVERITY"] == "PREMIUM"]),
    }

    st.dataframe(pd.DataFrame([summary_data]), use_container_width=True)

    st.subheader("📋 Data Monitoring Tiket Aktif")

    df_display = df_active[
        [
            "INCIDENT",
            "WITEL",
            "LAYANAN",
            "JENIS_GANGGUAN",
            "SEVERITY",
            "UMUR_TIKET_HARI"
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
            "SUMMARY",
            "REPORTED DATE",
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
