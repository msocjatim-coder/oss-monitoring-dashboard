import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="OSS Monitoring Dashboard", layout="wide")

st.title("📊 OSS Monitoring Dashboard")

uploaded_file = st.file_uploader("Upload File CSV dari OSS", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

df.columns = df.columns.str.strip()
df.columns = df.columns.str.replace('"', '')
df.columns = df.columns.str.replace(',', '')

required_columns = ["INCIDENT", "STATUS", "WITEL", "REPORTED DATE"]
    st.success("File berhasil diupload!")

    # Pastikan kolom penting ada
    required_columns = ["INCIDENT", "STATUS", "WITEL", "REPORTED DATE"]

    missing_cols = [col for col in required_columns if col not in df.columns]

    if missing_cols:
        st.error(f"Kolom berikut tidak ditemukan: {missing_cols}")
    else:
        # Konversi tanggal
        df["REPORTED DATE"] = pd.to_datetime(df["REPORTED DATE"], errors="coerce")

        # Hitung umur tiket
        df["UMUR_TIKET_HARI"] = (datetime.now() - df["REPORTED DATE"]).dt.days

        # Tentukan tiket aktif
        df["IS_ACTIVE"] = ~df["STATUS"].str.lower().isin(["closed", "resolved", "cancel"])

        st.subheader("🔎 Filter Data")

        witel_filter = st.selectbox("Filter Witel", ["Semua"] + sorted(df["WITEL"].dropna().unique().tolist()))

        if witel_filter != "Semua":
            df = df[df["WITEL"] == witel_filter]

        show_active_only = st.checkbox("Tampilkan hanya tiket aktif")

        if show_active_only:
            df = df[df["IS_ACTIVE"] == True]

        st.subheader("📈 Ringkasan")
        col1, col2 = st.columns(2)
        col1.metric("Total Tiket", len(df))
        col2.metric("Tiket Aktif", df["IS_ACTIVE"].sum())

        st.subheader("📋 Data Tiket")
        st.dataframe(df, use_container_width=True)

        # Download hasil filter
        csv_download = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇ Download Data (CSV)",
            data=csv_download,
            file_name="hasil_monitoring.csv",
            mime="text/csv"
        )
