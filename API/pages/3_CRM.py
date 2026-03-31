import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection

st.set_page_config(page_title="CRM Vault | PropIntel", layout="wide")

if not st.session_state.get("user_email"):
    st.warning("Please log in from the main page.")
    st.stop()

st.title("📂 Enterprise CRM Vault")
st.write("Review, filter, and export your previously analyzed intelligence.")

try:
    conn = st.connection("supabase", type=SupabaseConnection)
    data = conn.table("saved_leads").select("*").eq("user_email", st.session_state.user_email).execute()
    
    if data.data:
        df = pd.DataFrame(data.data)
        df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        
        # Filtering tools for the CRM
        score_filter = st.slider("Filter by Minimum Score", 1, 10, 1)
        
        # Ensure 'score' is numeric for filtering
        df['score_num'] = pd.to_numeric(df['score'], errors='coerce').fillna(0)
        filtered_df = df[df['score_num'] >= score_filter]
        
        # Drop the temp column and display
        filtered_df = filtered_df.drop(columns=['id', 'user_email', 'score_num'])
        st.dataframe(filtered_df, use_container_width=True)
        
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export CRM to CSV", data=csv, file_name="propintel_crm_export.csv")
    else:
        st.info("Your CRM is empty. Go to the Lead Analyzer to process and save leads.")
except Exception as e:
    st.error("Could not connect to CRM Database. Please check your Supabase configuration.")