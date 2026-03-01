import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import os

st.set_page_config(page_title="OSS Monitoring Dashboard", layout="wide")

DATA_FILE = "oss_data_shared.csv"
TIME_FILE = "last_update_time.txt"

wib = ZoneInfo("Asia/Jakarta")

st.markdown("""
<style>
/* Upload button jadi persegi panjang & efisien */
[data-testid="stFileUploader"] { max-width: 260px; }
[data-testid="stFileUploader"] section { padding: 6px 12px 6px 12px; }
[data-testid="stFileUploader"] div[role="button"] { min-height: 55px; border-radius: 8px; }

/* Animasi kedap-kedip */
@keyframes blink {0% { opacity: 1; }50% { opacity: 0.2; }100% { opacity: 1; }}
.blink-text { animation: blink 1.2s infinite; font-weight: bold; color: white; font-size: 16px; text-align: center;}
</style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([8, 2])
with col1:
    st.title("📊 OSS Monitoring Dashboard")
with col2:
    uploaded_files = st.file_uploader("", type=["csv"], accept_multiple_files=True, label_visibility="collapsed")

if uploaded_files:
    df_list = []
    for uploaded_file in uploaded_files:
        try: df_temp = pd.read_csv(uploaded_file)
        except: df_temp = pd.read_csv(uploaded_file, encoding="latin1")
        df_temp.columns = df_temp.columns.str.strip().str.replace('"', '', regex=False).str.replace(',', '', regex=False)
        df_list.append(df_temp)
    df = pd.concat(df_list, ignore_index=True)
    df.to_csv(DATA_FILE, index=False)
    now_time = datetime.now(wib).strftime("%H:%M")
    with open(TIME_FILE, "w") as f: f.write(now_time)
    st.success("Data berhasil diperbarui & tersimpan.")

if not os.path.exists(DATA_FILE):
    st.warning("Belum ada data. Silakan upload terlebih dahulu.")
    st.stop()
df = pd.read_csv(DATA_FILE)

if os.path.exists(TIME_FILE):
    with open(TIME_FILE, "r") as f: last_update = f.read().strip()
    if last_update: st.markdown(f'<div class="blink-text">Data Diperbarui pada {last_update} WIB</div>', unsafe_allow_html=True)

st.markdown("---")

required_columns = ["INCIDENT", "STATUS", "WITEL", "REPORTED DATE", "SUMMARY"]
missing_cols = [col for col in required_columns if col not in df.columns]
if missing_cols: st.error(f"Kolom berikut tidak ditemukan: {missing_cols}"); st.stop()

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

tab1, tab2, tab3 = st.tabs(["TIKET AKTIF", "TIKET CLOSE", "DOWNLOAD TIKET"])

with tab1:
    df_active = df[df["IS_ACTIVE"] == True].copy()
    df_display = df_active[
        ["INCIDENT","WITEL","LAYANAN","SERVICE ID","JENIS_GANGGUAN","SEVERITY","TTR CUSTOMER","LAST UPDATE WORKLOG","WORKLOG SUMMARY"]
    ].copy()
    # Format TTR CUSTOMER: 47:24:41 → 47 jam 24 menit
    def format_ttr_customer(ttr):
        if not isinstance(ttr, str) or not ttr: return ttr
        parts = ttr.split(":")
        if len(parts) != 3: return ttr
        jam, menit, _ = parts
        return f"{int(jam)} jam {int(menit)} menit"
    df_display["TTR CUSTOMER"] = df_display["TTR CUSTOMER"].apply(format_ttr_customer)
    # Format LAST UPDATE WORKLOG: 2026-03-01 08:11:49.399 → 08:11
    df_display["LAST UPDATE WORKLOG"] = pd.to_datetime(df_display["LAST UPDATE WORKLOG"], errors='coerce').dt.strftime('%H:%M')
    df_display.index = range(1, len(df_display)+1)
    def highlight_severity_column(val):
        color_map = {"PREMIUM":"background-color:#800000;color:white;","CRITICAL":"background-color:red;color:white;",
                     "MAJOR":"background-color:orange;","MINOR":"background-color:yellow;","LOW":"background-color:lightgreen;"}
        return color_map.get(val,"")
    styled_df = df_display.style.applymap(highlight_severity_column, subset=["SEVERITY"])
    st.dataframe(styled_df, use_container_width=True)

with tab2:
    df_close = df[df["IS_ACTIVE"] == False].copy()
    if "CLOSE" not in df_close.columns: df_close["CLOSE"] = "-"
    df_close["CLOSE"] = df_close["CLOSE"].fillna("-")
    if "SALSIM" not in df_close.columns: df_close["SALSIM"] = "-"
    df_close_display = df_close[["INCIDENT","WITEL","SUMMARY","REPORTED DATE","SALSIM","CLOSE"]].copy()
    df_close_display.index = range(1, len(df_close_display)+1)
    st.dataframe(df_close_display, use_container_width=True)

with tab3:
    csv_download = df.to_csv(index=False).encode("utf-8")
    st.download_button(label="Download Semua Data (CSV)", data=csv_download, file_name="oss_full_data.csv", mime="text/csv")
