import streamlit as st
import pandas as pd
import requests
import time

# --- 1. BRANDING & CONFIG ---
st.set_page_config(page_title="PropIntel Engine", page_icon="🏢", layout="wide")
st.title("🏢 PropIntel Engine")

# --- 2. API KEY MANAGEMENT ---
with st.sidebar:
    st.header("🔑 Connection Settings")
    
    # Check for Groq instead of OpenAI
    sc_groq = st.secrets.get("GROQ_API_KEY", "")
    sc_attom = st.secrets.get("ATTOM_API_KEY", "")

    groq_key = st.text_input("Groq API Key (Free)", value=sc_groq, type="password")
    attom_key = st.text_input("ATTOM API Key", value=sc_attom, type="password")
    
    if not groq_key:
        st.info("💡 Get a free AI key at console.groq.com")
# --- 3. CORE LOGIC ---

def get_property_data(address, city_state):
    """Fetches public records from ATTOM."""
    if not attom_key: return None
    
    url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/address"
    headers = {"apikey": attom_key, "Accept": "application/json"}
    params = {"address1": address, "address2": city_state}
    
    try:
        r = requests.get(url, headers=headers, params=params, timeout=5)
        data = r.json()
        if "property" in data and data["property"]:
            p = data['property'][0]
            # Fallback for hidden owner names in trial keys
            owner = p.get('status', {}).get('ownerName', "Contact for Owner")
            return {"owner": owner}
        return {"owner": "Unknown Entity"}
    except:
        return {"owner": "Data Unavailable"}

def get_free_ai_hook(owner_name, address):
    """Uses Groq (Llama 3.3) for free AI generation."""
    if not groq_key:
        return "5", "Please provide Groq Key for AI hooks."

    # Groq uses the same structure as OpenAI!
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
    
    prompt = f"Property: {address}. Owner: {owner_name}. Task: Score lead 1-10 and write a 2-sentence broker email hook. Return ONLY: SCORE: X | HOOK: Text"
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        resp = requests.post(url, json=payload, headers=headers)
        res_text = resp.json()['choices'][0]['message']['content']
        score = res_text.split('|')[0].replace("SCORE:", "").strip()
        hook = res_text.split('|')[1].replace("HOOK:", "").strip()
        return score, hook
    except:
        return "N/A", "AI busy or key error."

# --- 4. THE UI ---

uploaded_file = st.file_uploader("Upload Lead CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if st.button("🚀 Run Free Engine"):
        results = []
        progress = st.progress(0)
        
        for i, row in df.iterrows():
            addr = row.get('Address') or row.get('address')
            cs = row.get('CityState') or row.get('citystate')
            
            if addr:
                # 1. Get Data
                prop = get_property_data(addr, cs)
                # 2. Get AI
                score, hook = get_free_ai_hook(prop['owner'], addr)
                
                results.append({
                    "Address": addr,
                    "Actual Owner": prop['owner'],
                    "PropIntel Score": score,
                    "Personalized Hook": hook
                })
            progress.progress((i + 1) / len(df))
        
        if results:
            st.success("Done! Processed with 0 cost.")
            st.dataframe(pd.DataFrame(results))