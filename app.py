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
            df = pd.read_csv(uploaded_file)
        except:
            df = pd.read_csv(uploaded_file, encoding="latin1")

        # Bersihkan nama kolom
        df.columns = df.columns.str.strip()
        df.columns = df.columns.str.replace('"', '', regex=False)
        df.columns = df.columns.str.replace(',', '', regex=False)

        df_list.append(df)

    # Gabungkan semua file
    df = pd.concat(df_list, ignore_index=True)

    st.success(f"{len(uploaded_files)} file berhasil digabung!")

    required_columns = ["INCIDENT", "STATUS", "WITEL", "REPORTED DATE"]

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

        st.subheader("🔎 Filter Data")

        witel_list = sorted(df["WITEL"].dropna().unique().tolist())
        witel_filter = st.selectbox("Filter Witel", ["Semua"] + witel_list)

        if witel_filter != "Semua":
            df = df[df["WITEL"] == witel_filter]

        show_active_only = st.checkbox("Tampilkan hanya tiket aktif")

        if show_active_only:
            df = df[df["IS_ACTIVE"] == True]

        st.subheader("📈 Ringkasan")
        col1, col2 = st.columns(2)
        col1.metric("Total Tiket", len(df))
        col2.metric("Tiket Aktif", int(df["IS_ACTIVE"].sum()))

        st.subheader("📋 Data Tiket")

        # Index mulai dari 1
        df_display = df.copy()
        df_display.index = range(1, len(df_display) + 1)

        st.dataframe(df_display, use_container_width=True)

        # Tombol download
        csv_download = df_display.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇ Download Data (CSV)",
            data=csv_download,
            file_name="hasil_monitoring.csv",
            mime="text/csv"
        )
