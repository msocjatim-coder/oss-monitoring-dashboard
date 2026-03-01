import streamlit as st
import pandas as pd
from datetime import datetime
import os
import pytz

st.set_page_config(page_title="OSS Monitoring Dashboard", layout="wide")

DATA_FILE = "oss_data_shared.csv"
TIME_FILE = "last_update_time.txt"

# ======================= TIMEZONE WIB =======================
wib = pytz.timezone("Asia/Jakarta")

# ======================= CUSTOM CSS =========================
st.markdown("""
<style>

/* Upload button persegi panjang */
[data-testid="stFileUploader"] {
    max-width: 260px;
}
[data-testid="stFileUploader"] section {
    padding: 6px 12px 6px 12px;
}
[data-testid="stFileUploader"] div[role="button"] {
    min-height: 55px;
    border-radius: 8px;
}

/* Blink putih */
@keyframes blink {
    0% { opacity: 1; }
    50% { opacity: 0.3; }
    100% { opacity: 1; }
}

.blink-text {
    animation: blink 1.2s infinite;
    font-weight: bold;
    color: white;
    font-size: 16px;
}

</style>
""", unsafe_allow_html=True)

# ======================= HEADER =============================
col1, col2 = st.columns([8, 2])

with col1:
    st.title("📊 OSS Monitoring Dashboard")

with col2:
    uploaded_files = st.file_uploader(
        "",
        type=["csv"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

# ======================= HANDLE UPLOAD ======================
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

    now_time = datetime.now(wib).strftime("%H:%M")
    with open(TIME_FILE, "w") as f:
        f.write(now_time)

    st.success("Data berhasil diperbarui & tersimpan.")

# ======================= LOAD DATA ==========================
if not os.path.exists(DATA_FILE):
    st.warning("Belum ada data. Silakan upload terlebih dahulu.")
    st.stop()

df = pd.read_csv(DATA_FILE)

# ======================= TAMPILKAN JAM UPDATE ===============
if os.path.exists(TIME_FILE):
    with open(TIME_FILE, "r") as f:
        last_update = f.read().strip()
else:
    last_update = "-"

st.markdown(
    f'<div class="blink-text">Data Diperbarui pada {last_update} WIB</div>',
    unsafe_allow_html=True
)

st.markdown("---")

# ======================= VALIDASI ===========================
required_columns = ["INCIDENT", "STATUS", "WITEL", "REPORTED DATE", "SUMMARY"]
missing_cols = [col for col in required_columns if col not in df.columns]

if missing_cols:
    st.error(f"Kolom berikut tidak ditemukan: {missing_cols}")
    st.stop()

# ======================= PROCESSING (TIDAK DIUBAH) ==========
df = df.drop_duplicates(subset=["INCIDENT"])
df["REPORTED DATE"] = pd.to_datetime(df["REPORTED DATE"], errors="coerce")
df["UMUR_TIKET_HARI"] = (datetime.now(wib) - df["REPORTED DATE"]).dt.days

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

# ======================= MENU ===============================
tab1, tab2, tab3 = st.tabs(
    ["TIKET AKTIF", "TIKET CLOSE", "DOWNLOAD TIKET"]
)

# ======================= TIKET AKTIF ========================
with tab1:

    df_active = df[df["IS_ACTIVE"] == True].copy()

    st.subheader("📋 Data Monitoring Tiket Aktif")

    for i, row in df_active.iterrows():
        col_main, col_copy = st.columns([20, 1])

        with col_main:
            st.write({
                "INCIDENT": row.get("INCIDENT"),
                "WITEL": row.get("WITEL"),
                "LAYANAN": row.get("LAYANAN"),
                "SERVICE ID": row.get("SERVICE ID"),
                "JENIS_GANGGUAN": row.get("JENIS_GANGGUAN"),
                "SEVERITY": row.get("SEVERITY"),
                "TTR CUSTOMER": row.get("TTR CUSTOMER"),
                "LAST UPDATE WORKLOG": row.get("LAST UPDATE WORKLOG"),
                "WORKLOG SUMMARY": row.get("WORKLOG SUMMARY")
            })

        with col_copy:
            copy_text = f"""mohon dibantu kembali info progres saat ini 🙏
update terakhir : {row.get("WORKLOG SUMMARY", "")}"""

            st.code(copy_text, language="")

# ======================= TIKET CLOSE ========================
with tab2:

    df_close = df[df["IS_ACTIVE"] == False].copy()

    if "CLOSE" not in df_close.columns:
        df_close["CLOSE"] = "-"

    df_close["CLOSE"] = df_close["CLOSE"].fillna("-")

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

# ======================= DOWNLOAD ===========================
with tab3:

    csv_download = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Semua Data (CSV)",
        data=csv_download,
        file_name="oss_full_data.csv",
        mime="text/csv"
    )
