import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="OSS Monitoring Dashboard", layout="wide")

st.title("📊 OSS Monitoring Dashboard")

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

        # Bersihkan nama kolom
        df_temp.columns = df_temp.columns.str.strip()
        df_temp.columns = df_temp.columns.str.replace('"', '', regex=False)
        df_temp.columns = df_temp.columns.str.replace(',', '', regex=False)

        df_list.append(df_temp)

    # Gabungkan semua file
    df = pd.concat(df_list, ignore_index=True)

    st.success(f"{len(uploaded_files)} file berhasil digabung!")

    required_columns = ["INCIDENT", "STATUS", "WITEL", "REPORTED DATE", "SUMMARY"]

    missing_cols = [col for col in required_columns if col not in df.columns]

    if missing_cols:
        st.error(f"Kolom berikut tidak ditemukan: {missing_cols}")
    else:
        # Hapus duplikat berdasarkan INCIDENT
        df = df.drop_duplicates(subset=["INCIDENT"])

        # Konversi tanggal
        df["REPORTED DATE"] = pd.to_datetime(df["REPORTED DATE"], errors="coerce")

        # Hitung umur tiket
        df["UMUR_TIKET_HARI"] = (datetime.now() - df["REPORTED DATE"]).dt.days

        # Tentukan tiket aktif
        df["IS_ACTIVE"] = ~df["STATUS"].str.lower().isin(
            ["closed", "resolved", "cancel"]
        )

        # ===============================
        # AUTO DETEKSI DARI SUMMARY
        # ===============================

        df["SUMMARY"] = df["SUMMARY"].astype(str)

        # LAYANAN
        df["LAYANAN"] = df["SUMMARY"].apply(
            lambda x: "TSEL" if "TSEL" in x.upper() else "OLO"
        )

        # JENIS
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

        # SEVERITY
        severity_list = ["PREMIUM", "CRITICAL", "MAJOR", "MINOR", "LOW"]

        def detect_severity(summary):
            summary = summary.upper()
            for sev in severity_list:
                if sev in summary:
                    return sev
            return "-"

        df["SEVERITY"] = df["SUMMARY"].apply(detect_severity)

        # ===============================
        # FILTER
        # ===============================

        st.subheader("🔎 Filter Data")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            witel_list = sorted(df["WITEL"].dropna().unique().tolist())
            witel_filter = st.selectbox("Filter Witel", ["Semua"] + witel_list)

        with col2:
            layanan_filter = st.selectbox(
                "Filter Layanan",
                ["Semua"] + sorted(df["LAYANAN"].unique())
            )

        with col3:
            jenis_filter = st.selectbox(
                "Filter Jenis",
                ["Semua"] + sorted(df["JENIS_GANGGUAN"].unique())
            )

        with col4:
            severity_filter = st.selectbox(
                "Filter Severity",
                ["Semua"] + sorted(df["SEVERITY"].unique())
            )

        if witel_filter != "Semua":
            df = df[df["WITEL"] == witel_filter]

        if layanan_filter != "Semua":
            df = df[df["LAYANAN"] == layanan_filter]

        if jenis_filter != "Semua":
            df = df[df["JENIS_GANGGUAN"] == jenis_filter]

        if severity_filter != "Semua":
            df = df[df["SEVERITY"] == severity_filter]

        show_active_only = st.checkbox("Tampilkan hanya tiket aktif")

        if show_active_only:
            df = df[df["IS_ACTIVE"] == True]

        # ===============================
        # RINGKASAN
        # ===============================

        st.subheader("📈 Ringkasan")

        colA, colB, colC = st.columns(3)

        colA.metric("Total Tiket", len(df))
        colB.metric("Tiket Aktif", int(df["IS_ACTIVE"].sum()))
        colC.metric(
            "Critical / Major",
            int(df[df["SEVERITY"].isin(["CRITICAL", "MAJOR"])].shape[0])
        )

        # ===============================
        # DATA MONITORING (HANYA 6 KOLOM)
        # ===============================

        st.subheader("📋 Data Monitoring")

        df_display = df[
            [
                "INCIDENT",
                "WITEL",
                "SERVICE ID",
                "TTR CUSTOMER",
                "LAST UPDATE WORKLOG",
                "WORKLOG SUMMARY",
            ]
        ].copy()

        df_display.index = range(1, len(df_display) + 1)

        # Pewarnaan berdasarkan severity
        def highlight_severity(row):
            color_map = {
                "PREMIUM": "background-color: #800000; color: white;",
                "CRITICAL": "background-color: red; color: white;",
                "MAJOR": "background-color: orange;",
                "MINOR": "background-color: yellow;",
                "LOW": "background-color: lightgreen;",
            }
            severity = df.loc[row.name, "SEVERITY"]
            return [color_map.get(severity, "")] * len(row)

        st.dataframe(
            df_display.style.apply(highlight_severity, axis=1),
            use_container_width=True
        )

        # Download sesuai tampilan
        csv_download = df_display.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇ Download Data Monitoring (CSV)",
            data=csv_download,
            file_name="hasil_monitoring.csv",
            mime="text/csv"
        )
