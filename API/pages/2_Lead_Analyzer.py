import streamlit as st
import pandas as pd
import requests
import time
from st_supabase_connection import SupabaseConnection

st.set_page_config(page_title="Analyzer | PropIntel", layout="wide")

if not st.session_state.get("user_email"):
    st.warning("Please log in from the main page.")
    st.stop()

st.title("🚀 Lead Analyzer")
st.write("Upload your raw address list to pierce LLCs and generate AI outreach hooks.")

# Fetch BYOK keys from Session State
groq_key = st.session_state.get("groq_key", "")
attom_key = st.session_state.get("attom_key", "")

def process_lead(address, city_state):
    # ATTOM Data Fetch
    owner = "Entity Hidden"
    if attom_key:
        url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/address"
        headers = {"apikey": attom_key, "Accept": "application/json"}
        try:
            r = requests.get(url, headers=headers, params={"address1": address, "address2": city_state}, timeout=5)
            if "property" in r.json() and r.json()["property"]:
                owner = r.json()['property'][0].get('status', {}).get('ownerName', "Entity Hidden")
        except: pass

    # Groq AI Hook Generation
    score, hook = "N/A", "Please configure Groq API Key in Settings."
    if groq_key:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": f"Score lead 1-10 and write a 1-sentence broker pitch for {address} owned by {owner}. Format: SCORE: X | HOOK: Text"}]
        }
        try:
            resp = requests.post(url, json=payload, headers=headers)
            text = resp.json()['choices'][0]['message']['content']
            score = text.split('|')[0].replace("SCORE:", "").strip()
            hook = text.split('|')[1].replace("HOOK:", "").strip()
        except: pass
        
    return owner, score, hook

uploaded_file = st.file_uploader("Upload CSV (Address, CityState)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if st.button("Execute Engine"):
        if not groq_key or not attom_key:
            st.error("⚠️ API Keys missing! Please set them up in the Settings tab.")
            st.stop()
            
        results = []
        bar = st.progress(0)
        for i, row in df.iterrows():
            addr = row.get('Address', '')
            cs = row.get('CityState', '')
            owner, score, hook = process_lead(addr, cs)
            
            results.append({
                "Address": addr, "CityState": cs, "Owner": owner, "Score": score, "Hook": hook
            })
            bar.progress((i + 1) / len(df))
            
        res_df = pd.DataFrame(results)
        st.session_state.latest_run = res_df
        st.success("Analysis Complete!")
        st.dataframe(res_df, use_container_width=True)

if "latest_run" in st.session_state:
    if st.button("💾 Save to CRM"):
        try:
            conn = st.connection("supabase", type=SupabaseConnection)
            for _, r in st.session_state.latest_run.iterrows():
                conn.table("saved_leads").insert({
                    "user_email": st.session_state.user_email,
                    "address": r['Address'],
                    "owner_name": r['Owner'],
                    "score": r['Score'],
                    "hook": r['Hook']
                }).execute()
            st.success("Successfully synced to CRM Vault!")
        except Exception as e:
            st.error(f"Database error: Ensure Supabase secrets are set. ({e})")