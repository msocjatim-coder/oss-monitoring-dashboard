import streamlit as st
import pandas as pd
from datetime import datetime

# Import components
from components.sidebar import ModernSidebar
from components.dashboard import ModernDashboard
from database.db_handler import DatabaseHandler
from utils.csv_processor import CSVProcessor
from models.data_model import OSSData
import config

# Page config
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout=config.APP_LAYOUT,
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Modern styling */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Card styling */
    .css-1r6slb0 {
        border-radius: 1rem;
        padding: 1.5rem;
        background: rgba(255, 255, 255, 0.95);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.18);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        border-radius: 1rem;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'db_handler' not in st.session_state:
    st.session_state.db_handler = DatabaseHandler()
if 'csv_processor' not in st.session_state:
    st.session_state.csv_processor = CSVProcessor()

# Render sidebar and get navigation
nav = ModernSidebar.render()
page = nav['page']
filters = nav['filters']

# Main content area
if page == "Dashboard":
    # Load data from database
    with st.spinner("Loading data..."):
        data = st.session_state.db_handler.get_all_oss_data()
    
    # Render dashboard
    ModernDashboard.render(data, filters)

elif page == "Upload Data":
    st.markdown("## 📤 Upload Data OSS")
    
    # File uploader dengan desain modern
    uploaded_file = st.file_uploader(
        "Upload CSV File",
        type=['csv'],
        help="Upload file CSV dengan format yang sesuai"
    )
    
    if uploaded_file is not None:
        # Validasi CSV
        is_valid, message, df = st.session_state.csv_processor.validate_csv(uploaded_file)
        
        if is_valid:
            st.success(f"✅ {message}")
            
            # Preview data
            st.markdown("### 👁️ Preview Data")
            st.dataframe(df.head(), use_container_width=True)
            
            # Show data statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"📊 Total Rows: {len(df)}")
            with col2:
                st.info(f"📋 Total Columns: {len(df.columns)}")
            with col3:
                st.info(f"🏷️ Regions: {df['region'].nunique() if 'region' in df.columns else 'N/A'}")
            
            # Confirm upload button
            if st.button("🚀 Upload to Database", type="primary", use_container_width=True):
                with st.spinner("Processing data..."):
                    # Process data
                    success, msg, oss_data, summary = st.session_state.csv_processor.process_upload(df)
                    
                    if success:
                        # Insert to database
                        response = st.session_state.db_handler.insert_oss_data(df)
                        
                        if response:
                            st.success(f"✅ {msg}")
                            
                            # Show upload summary
                            st.markdown("### 📊 Upload Summary")
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Total Sites", summary['total_sites'])
                            with col2:
                                st.metric("Active Sites", summary['active_sites'])
                            with col3:
                                st.metric("Avg Uptime", f"{summary['avg_uptime']:.1f}%")
                            with col4:
                                st.metric("Total Alerts", summary['total_alerts'])
                            
                            st.balloons()
                        else:
                            st.error("❌ Gagal menyimpan ke database")
                    else:
                        st.error(f"❌ {msg}")
        else:
            st.error(f"❌ {message}")
            
            # Template download
            st.markdown("### 📥 Download Template")
            template_df = pd.DataFrame({
                'site_id': ['SITE001', 'SITE002'],
                'site_name': ['Site Jakarta 1', 'Site Bandung 1'],
                'region': ['Jakarta', 'Bandung'],
                'status': ['Active', 'Maintenance'],
                'uptime_percentage': [99.5, 98.2],
                'bandwidth_usage': [150.5, 200.3],
                'last_maintenance': ['2024-01-15', '2024-01-20'],
                'alert_count': [0, 2]
            })
            
            csv = template_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV Template",
                data=csv,
                file_name="oss_template.csv",
                mime="text/csv"
            )

elif page == "Data Viewer":
    st.markdown("## 📋 Data Viewer")
    
    # Load data
    data = st.session_state.db_handler.get_all_oss_data()
    
    if not data.empty:
        # Data statistics
        st.markdown("### 📊 Data Statistics")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Records", len(data))
        with col2:
            st.metric("Total Sites", data['site_id'].nunique() if 'site_id' in data.columns else 'N/A')
        with col3:
            st.metric("Last Update", data['created_at'].max()[:10] if 'created_at' in data.columns else 'N/A')
        with col4:
            st.metric("Data Volume", f"{data.memory_usage(deep=True).sum() / 1024:.1f} KB")
        
        # Data table with search
        st.markdown("### 🔍 Data Table")
        
        # Search box
        search = st.text_input("🔎 Search...", placeholder="Cari site name atau region...")
        
        if search:
            mask = data['site_name'].str.contains(search, case=False) | data['region'].str.contains(search, case=False)
            filtered_data = data[mask]
        else:
            filtered_data = data
        
        # Display data with styling
        st.dataframe(
            filtered_data,
            use_container_width=True,
            hide_index=True,
            column_config={
                "site_id": "Site ID",
                "site_name": "Site Name",
                "region": "Region",
                "status": st.column_config.TextColumn(
                    "Status",
                    help="Current status of the site"
                ),
                "uptime_percentage": st.column_config.NumberColumn(
                    "Uptime %",
                    format="%.2f %%"
                ),
                "bandwidth_usage": st.column_config.NumberColumn(
                    "Bandwidth (Mbps)",
                    format="%.1f Mbps"
                ),
                "alert_count": st.column_config.NumberColumn(
                    "Alerts",
                    format="%d ⚠️"
                ),
                "created_at": st.column_config.DatetimeColumn(
                    "Created At",
                    format="DD/MM/YYYY HH:mm"
                )
            }
        )
        
        # Export button
        if st.button("📥 Export to CSV", use_container_width=True):
            csv = data.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"oss_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.info("📭 No data available. Please upload data first.")

elif page == "Settings":
    st.markdown("## ⚙️ Settings")
    
    # Database settings
    st.markdown("### 🗄️ Database Settings")
    
    # Show connection status
    try:
        test = st.session_state.db_handler.get_all_oss_data()
        st.success("✅ Database connection: OK")
    except:
        st.error("❌ Database connection: Failed")
    
    # Data management
    st.markdown("### 🗑️ Data Management")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧹 Clear All Data", type="secondary", use_container_width=True):
            if st.session_state.db_handler.delete_all_data():
                st.success("✅ All data cleared")
                st.rerun()
            else:
                st.error("❌ Failed to clear data")
    
    with col2:
        # Backup data
        data = st.session_state.db_handler.get_all_oss_data()
        if not data.empty:
            csv = data.to_csv(index=False)
            st.download_button(
                label="💾 Backup Data",
                data=csv,
                file_name=f"oss_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    # App settings
    st.markdown("### 🎨 Appearance")
    
    theme = st.selectbox(
        "Theme",
        ["Light", "Dark", "System"],
        index=0
    )
    
    chart_style = st.selectbox(
        "Chart Style",
        ["Modern", "Classic", "Minimal"],
        index=0
    )
    
    if st.button("💾 Save Settings", type="primary"):
        st.success("✅ Settings saved!")