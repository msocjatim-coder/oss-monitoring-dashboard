import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="OSS Monitoring Dashboard", layout="wide")

st.title("📊 OSS Monitoring Dashboard")

# ================= MENU BAR =================
menu = st.radio(
    "",
    ["TIKET AKTIF", "TIKET CLOSE", "DOWNLOAD TIKET"],
    horizontal=True
)

uploaded_files = st.file_uploader(
    "Upload Semua File CSV dari OSS (Bisa banyak sekaligus)",
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

    st.success(f"{len(uploaded_files)} file berhasil digabung!")

    required_columns = ["INCIDENT", "STATUS", "WITEL", "REPORTED DATE", "SUMMARY"]
    missing_cols = [col for col in required_columns if col not in df.columns]

    if missing_cols:
        st.error(f"Kolom berikut tidak ditemukan: {missing_cols}")
    else:

        df = df.drop_duplicates(subset=["INCIDENT"])

        df["REPORTED DATE"] = pd.to_datetime(df["REPORTED DATE"], errors="coerce")
        df["UMUR_TIKET_HARI"] = (datetime.now() - df["REPORTED DATE"]).dt.days

        df["IS_ACTIVE"] = ~df["STATUS"].str.lower().isin(
            ["closed", "resolved", "cancel"]
        )

        df["SUMMARY"] = df["SUMMARY"].astype(str)

        # ================= AUTO DETEKSI =================

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

        # ================= FORMAT TTR =================

        if "TTR CUSTOMER" in df.columns:
            def format_ttr(val):
                try:
                    parts = str(val).split(":")
                    hours = int(parts[0])
                    minutes = int(parts[1])
                    return f"{hours} jam {minutes} menit"
                except:
                    return val

            df["TTR CUSTOMER"] = df["TTR CUSTOMER"].apply(format_ttr)

        # ================= FORMAT LAST UPDATE =================

        if "LAST UPDATE WORKLOG" in df.columns:
            df["LAST UPDATE WORKLOG"] = pd.to_datetime(
                df["LAST UPDATE WORKLOG"], errors="coerce"
            ).dt.strftime("%H:%M:%S")

        # ============================================================
        # ======================= TIKET AKTIF =========================
        # ============================================================

        if menu == "TIKET AKTIF":

            df_active = df[df["IS_ACTIVE"] == True].copy()

            st.subheader("📋 Data Monitoring Tiket Aktif")

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

            def highlight_severity(val):
                color_map = {
                    "PREMIUM": "background-color: #800000; color: white;",
                    "CRITICAL": "background-color: red; color: white;",
                    "MAJOR": "background-color: orange;",
                    "MINOR": "background-color: yellow;",
                    "LOW": "background-color: lightgreen;",
                }
                return color_map.get(val, "")

            styled_df = df_display.style.applymap(
                highlight_severity,
                subset=["SEVERITY"]
            )

            st.dataframe(styled_df, use_container_width=True)

        # ============================================================
        # ======================= TIKET CLOSE =========================
        # ============================================================

        elif menu == "TIKET CLOSE":

            df_close = df[df["IS_ACTIVE"] == False].copy()

            if "SALSIM" not in df_close.columns:
                df_close["SALSIM"] = "-"

            if "CLOSE" not in df_close.columns:
                df_close["CLOSE"] = "-"

            df_close["CLOSE"] = df_close["CLOSE"].fillna("-")

            st.subheader("📁 Data Tiket Close")

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
        # ======================= DOWNLOAD TIKET ======================
        # ============================================================

        elif menu == "DOWNLOAD TIKET":

            st.subheader("⬇ Download Semua Data Tiket")

            csv_download = df.to_csv(index=False).encode("utf-8")

            st.download_button(
                label="Download Semua Data OSS (CSV)",
                data=csv_download,
                file_name="oss_all_ticket.csv",
                mime="text/csv"
            )
