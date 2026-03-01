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
# ======================= CUSTOM CSS =========================
# ============================================================

st.markdown("""
<style>
/* ===== FILE UPLOADER: Tombol Browse di sebelah kanan teks ===== */
[data-testid="stFileUploader"] section {
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    justify-content: space-between !important;
    gap: 10px;
    padding: 6px 12px 6px 12px !important;
}

[data-testid="stFileUploader"] section label p {
    margin: 0;
    flex: 1;  /* teks Drag & Drop mengambil ruang maksimal */
}

[data-testid="stFileUploader"] div[role="button"] {
    min-height: 38px;
    border-radius: 8px;
    padding: 0 12px;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* Animasi kedap-kedip */
@keyframes blink {0% { opacity: 1; }50% { opacity: 0.2; }100% { opacity: 1; }}
.blink-text { animation: blink 1.2s infinite; font-weight: bold; color: white; font-size: 16px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# ======================= HEADER =============================
# ============================================================

col1, col2 = st.columns([8, 2])
with col1:
    st.title("📊 OSS Monitoring Dashboard")
with col2:
    uploaded_files = st.file_uploader("", type=["csv"], accept_multiple_files=True, label_visibility="collapsed")

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
        df_temp.columns = df_temp.columns.str.strip().str.replace('"', '', regex=False).str.replace(',', '', regex=False)
        df_list.append(df_temp)
    df = pd.concat(df_list, ignore_index=True)
    df.to_csv(DATA_FILE, index=False)
    now_time = datetime.now(wib).strftime("%H:%M")
    with open(TIME_FILE, "w") as f:
        f.write(now_time)
    st.success("Data berhasil diperbarui & tersimpan.")

# ============================================================
# ======================= LOAD DATA ==========================
# ============================================================

if not os.path.exists(DATA_FILE):
    st.warning("Belum ada data. Silakan upload terlebih dahulu.")
    st.stop()
df = pd.read_csv(DATA_FILE)

# ============================================================
# ======================= JAM UPDATE =========================
# ============================================================

if os.path.exists(TIME_FILE):
    with open(TIME_FILE, "r") as f:
        last_update = f.read().strip()
    if last_update:
        st.markdown(f'<div class="blink-text">Data Diperbarui pada {last_update} WIB</div>', unsafe_allow_html=True)

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
df["REPORTED DATE"] = pd.to_datetime(df["REPORTED DATE"], errors="coerce").dt.tz_localize(None)
now_naive = datetime.now(wib).replace(tzinfo=None)
df["UMUR_TIKET_HARI"] = (now_naive - df["REPORTED DATE"]).dt.days
df["IS_ACTIVE"] = ~df["STATUS"].str.lower().isin(["closed", "resolved", "cancel"])
df["SUMMARY"] = df["SUMMARY"].astype(str)
df["LAYANAN"] = df["SUMMARY"].apply(lambda x: "TSEL" if "TSEL" in x.upper() else "OLO")

def detect_jenis(summary):
    summary = summary.upper()
    if "RADIOIP" in summary: return "RADIOIP"
    elif "TOPOLO" in summary: return "TOPOLO"
    elif "METRO" in summary: return "METRO"
    elif "CNQ" in summary: return "CNQ"
    elif "SLD" in summary: return "SLD"
    else: return "-"
df["JENIS_GANGGUAN"] = df["SUMMARY"].apply(detect_jenis)

severity_list = ["PREMIUM", "CRITICAL", "MAJOR", "MINOR", "LOW"]
def detect_severity(summary):
    summary = summary.upper()
    for sev in severity_list:
        if sev in summary: return sev
    return "-"
df["SEVERITY"] = df["SUMMARY"].apply(detect_severity)

# ============================================================
# ======================= MENU BAR ===========================
# ============================================================

tab1, tab2, tab3 = st.tabs(["TIKET AKTIF", "TIKET CLOSE", "DOWNLOAD TIKET"])

# ============================================================
# ======================= TIKET AKTIF ========================
# ============================================================

with tab1:
    df_active = df[df["IS_ACTIVE"] == True].copy()
    df_display = df_active[["INCIDENT","WITEL","LAYANAN","SERVICE ID","JENIS_GANGGUAN","SEVERITY",
                            "TTR CUSTOMER","LAST UPDATE WORKLOG","WORKLOG SUMMARY"]].copy()
    
    # ========================== UPDATE TTR CUSTOMER ==========================
    def format_ttr_customer(ttr):
        if not isinstance(ttr, str) or not ttr: 
            return ttr
        parts = ttr.split(":")
        if len(parts) != 3:
            return ttr
        total_hours, minutes, _ = map(int, parts)
        days = total_hours // 24
        hours = total_hours % 24
        if days > 0:
            return f"{days} hari {hours} jam {minutes} menit"
        else:
            return f"{hours} jam {minutes} menit"
    df_display["TTR CUSTOMER"] = df_display["TTR CUSTOMER"].apply(format_ttr_customer)
    # ==========================================================================

    # Format LAST UPDATE WORKLOG
    df_display["LAST UPDATE WORKLOG"] = pd.to_datetime(df_display["LAST UPDATE WORKLOG"], errors='coerce').dt.strftime('%H:%M')
    
    df_display.index = range(1, len(df_display)+1)

    # ========================== HIGHLIGHT SEVERITY ==========================
    def highlight_severity_column(val):
        color_map = {"PREMIUM":"background-color:#800000;color:white;",
                     "CRITICAL":"background-color:red;color:white;",
                     "MAJOR":"background-color:orange;",
                     "MINOR":"background-color:yellow;",
                     "LOW":"background-color:lightgreen;"}
        return color_map.get(val,"")
    
    # ========================== DISPLAY DENGAN BUTTON =======================
    for i, row in df_display.iterrows():
        cols = st.columns([1,1,1,1,1,1,1,1,3,1])  # Kolom terakhir untuk button
        cols[0].write(row["INCIDENT"])
        cols[1].write(row["WITEL"])
        cols[2].write(row["LAYANAN"])
        cols[3].write(row["SERVICE ID"])
        cols[4].write(row["JENIS_GANGGUAN"])
        cols[5].markdown(f'<div style="{highlight_severity_column(row["SEVERITY"])}">{row["SEVERITY"]}</div>', unsafe_allow_html=True)
        cols[6].write(row["TTR CUSTOMER"])
        cols[7].write(row["LAST UPDATE WORKLOG"])
        cols[8].write(row["WORKLOG SUMMARY"])
        if cols[9].button("Tanya?", key=f"tanya_{row['INCIDENT']}"):
            st.info(f"Tanya button ditekan untuk tiket: {row['INCIDENT']}")
            
# ============================================================
# ======================= TIKET CLOSE ========================
# ============================================================

with tab2:
    df_close = df[df["IS_ACTIVE"] == False].copy()
    if "CLOSE" not in df_close.columns: df_close["CLOSE"] = "-"
    df_close["CLOSE"] = df_close["CLOSE"].fillna("-")
    if "SALSIM" not in df_close.columns: df_close["SALSIM"] = "-"
    df_close_display = df_close[["INCIDENT","WITEL","SUMMARY","REPORTED DATE","SALSIM","CLOSE"]].copy()
    df_close_display.index = range(1, len(df_close_display)+1)
    st.dataframe(df_close_display, use_container_width=True)

# ============================================================
# ======================= DOWNLOAD ===========================
# ============================================================

with tab3:
    csv_download = df.to_csv(index=False).encode("utf-8")
    st.download_button(label="Download Semua Data (CSV)", data=csv_download, file_name="oss_full_data.csv", mime="text/csv")
