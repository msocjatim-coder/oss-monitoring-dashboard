import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import os

st.set_page_config(page_title="OSS Monitoring Dashboard", layout="wide")

DATA_FILE = "oss_data_shared.csv"
TIME_FILE = "last_update_time.txt"

wib = ZoneInfo("Asia/Jakarta")

# ============================================================
# ======================= SESSION STATE ======================
# ============================================================

if "selected_message" not in st.session_state:
    st.session_state.selected_message = None

# ============================================================
# ======================= CUSTOM CSS =========================
# ============================================================

st.markdown("""
<style>

/* === FILE UPLOADER FIX === */
[data-testid="stFileUploader"] section {
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px 8px 12px;
}

[data-testid="stFileUploader"] div[role="button"] {
    margin-left: 10px;
    height: 38px;
    display: flex;
    align-items: center;
}

/* === FULL GRID BOX TABLE === */
.header-style {
    border: 1px solid #666;
    padding: 8px;
    font-weight: bold;
    text-align: center;
    background-color: #1f1f1f;
    color: white;
}

.row-style {
    border: 1px solid #666;
    padding: 8px;
}

/* === Animasi Jam Update === */
@keyframes blink {
    0% { opacity: 1; }
    50% { opacity: 0.2; }
    100% { opacity: 1; }
}

.blink-text {
    animation: blink 1.2s infinite;
    font-weight: bold;
    color: white;
    font-size: 16px;
    text-align: center;
}

.popup-box {
    border:2px solid #2196F3;
    padding:20px;
    border-radius:10px;
    background-color:#f0f8ff;
    margin-bottom:20px;
    white-space:pre-wrap;
    font-size:15px;

}

</style>
""", unsafe_allow_html=True)

# ============================================================
# ======================= HEADER =============================
# ============================================================

col1, col2 = st.columns([8, 2])

with col1:
    st.title("📊 OSS Monitoring Dashboard")

with col2:
    if st.session_state.selected_message is None:
        uploaded_files = st.file_uploader(
            "",
            type=["csv"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
    else:
        uploaded_files = None

# ============================================================
# ======================= POPUP AREA =========================
# ============================================================

if st.session_state.selected_message:

    st.markdown("### 📑 Pesan Siap Dikirim")

    st.markdown(
        f'<div class="popup-box">{st.session_state.selected_message}</div>',
        unsafe_allow_html=True
    )

    col_copy, col_close = st.columns([1,1])

    with col_copy:
        if st.button("Copy Pesan"):
            st.code(st.session_state.selected_message)
            st.session_state.selected_message = None
            st.rerun()

    with col_close:
        if st.button("Tutup"):
            st.session_state.selected_message = None
            st.rerun()

# ============================================================
# ======================= HANDLE UPLOAD ======================
# ============================================================

if uploaded_files is not None and len(uploaded_files) > 0:

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

    # SIMPAN PERMANEN
    df_uploaded.to_csv(DATA_FILE, index=False)

    now_time = datetime.now(wib).strftime("%H:%M")
    with open(TIME_FILE, "w") as f:
        f.write(now_time)

    st.success("Data berhasil diperbarui & tersimpan.")

# ============================================================
# ======================= LOAD DATA ==========================
# ============================================================

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    st.warning("Belum ada data. Silakan upload terlebih dahulu.")
    st.stop()

# ============================================================
# ======================= JAM UPDATE =========================
# ============================================================

if os.path.exists(TIME_FILE):
    with open(TIME_FILE, "r") as f:
        last_update = f.read().strip()

    if last_update:
        st.markdown(
            f'<div class="blink-text">Data Diperbarui pada {last_update} WIB</div>',
            unsafe_allow_html=True
        )

st.markdown("---")

# ============================================================
# ======================= VALIDASI ===========================
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
df["REPORTED DATE"] = df["REPORTED DATE"].dt.tz_localize(None)
now_naive = datetime.now(wib).replace(tzinfo=None)
df["UMUR_TIKET_HARI"] = (now_naive - df["REPORTED DATE"]).dt.days

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
# ======================= MENU BAR ===========================
# ============================================================

tab1, tab2, tab3 = st.tabs(
    ["TIKET AKTIF", "TIKET CLOSE", "DOWNLOAD TIKET"]
)

# ============================================================
# ======================= TIKET AKTIF ========================
# ============================================================

with tab1:

    df_active = df[df["IS_ACTIVE"] == True].copy()
    df_active.insert(0, "NO", range(1, len(df_active) + 1))

    df_display = df_active[
        [
            "NO",
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

    # ===== HEADER =====
    header_cols = st.columns([0.5,1,1,1,1,1,1,1,1,2,1])
    headers = list(df_display.columns)

    for col, header in zip(header_cols[:-1], headers):
        col.markdown(f"<div class='header-style'>{header}</div>", unsafe_allow_html=True)

    header_cols[-1].markdown("")

    # ===== ROW DATA =====
    for i, row in df_display.iterrows():

        cols = st.columns([0.5,1,1,1,1,1,1,1,1,2,1])

        for idx, value in enumerate(row):
            cols[idx].markdown(f"<div class='row-style'>{value}</div>", unsafe_allow_html=True)

        # Tombol Tanya di kanan
        with cols[-1]:
            if st.button("Tanya", key=f"tanya_{i}"):

                message = (
                    "mohon dibantu kembali info progres saat ini 🙏\n"
                    f"update terakhir : {row['WORKLOG SUMMARY']}"
                )

                st.session_state.selected_message = message
                st.rerun()

# ============================================================
# ======================= TIKET CLOSE ========================
# ============================================================

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

# ============================================================
# ======================= DOWNLOAD ===========================
# ============================================================

with tab3:

    csv_download = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Semua Data (CSV)",
        data=csv_download,
        file_name="oss_full_data.csv",
        mime="text/csv"
    )
