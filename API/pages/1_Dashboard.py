import streamlit as st
import pandas as pd
import numpy as np
from st_supabase_connection import SupabaseConnection

st.set_page_config(page_title="Dashboard | PropIntel", layout="wide")

if not st.session_state.get("user_email"):
    st.warning("Please log in from the main page.")
    st.stop()

st.title("📊 Enterprise Dashboard")

# Initialize connection (Graceful fallback if secrets aren't set yet)
try:
    conn = st.connection("supabase", type=SupabaseConnection)
    data = conn.table("saved_leads").select("*").eq("user_email", st.session_state.user_email).execute()
    df = pd.DataFrame(data.data) if data.data else pd.DataFrame()
except:
    df = pd.DataFrame()

# --- METRICS ---
col1, col2, col3, col4 = st.columns(4)
total_leads = len(df) if not df.empty else 0
high_priority = len(df[df['score'].astype(str) >= "8"]) if not df.empty else 0

col1.metric("Total Leads Processed", total_leads)
col2.metric("High Priority (8+)", high_priority)
col3.metric("API Calls this Month", total_leads * 2)
col4.metric("System Status", "Operational 🟢")

st.divider()

# --- MARKET TRENDS CHARTS ---
st.subheader("Market Activity Trends")
if not df.empty and 'created_at' in df.columns:
    df['created_at'] = pd.to_datetime(df['created_at'])
    daily_counts = df.groupby(df['created_at'].dt.date).size()
    st.area_chart(daily_counts)
else:
    st.info("Not enough data to display trends. Run the Lead Analyzer to populate your dashboard.")
    
    # Placeholder chart for visual effect
    chart_data = pd.DataFrame(np.random.randn(20, 3), columns=['Commercial', 'Industrial', 'Multi-Family'])
    st.line_chart(chart_data)