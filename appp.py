import streamlit as st
import pandas as pd
import openai
import requests
import time

st.set_page_config(page_title="PropIntel Engine", page_icon="🏢", layout="wide")
st.title("🏢 PropIntel Engine (Debug Mode)")

# --- 1. CONFIG & SECRETS ---
with st.sidebar:
    st.header("🔑 Connection")
    # Priority: Secrets -> Manual Input
    sc_openai = st.secrets.get("OPENAI_API_KEY", "")
    sc_attom = st.secrets.get("ATTOM_API_KEY", "")
    openai_key = st.text_input("OpenAI API Key", value=sc_openai, type="password")
    attom_key = st.text_input("ATTOM API Key", value=sc_attom, type="password")
    use_mock = st.checkbox("Force Mock Mode (No APIs)", value=False)

# --- 2. THE ENGINE ---

def get_data(address, city_state):
    if use_mock:
        return {"owner": "Mock LLC", "last_sale": "2020-01-01", "price": "$1M", "year": "2000"}
    
    # DEBUG: Show what we are sending
    st.write(f"🔍 Searching ATTOM for: {address}, {city_state}")
    
    url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/detail"
    headers = {"apikey": attom_key, "Accept": "application/json"}
    params = {"address1": address, "address2": city_state}
    
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code != 200:
            st.error(f"❌ ATTOM Error {r.status_code}: {r.text}")
            return None
        data = r.json()
        p = data['property'][0]
        return {
            "owner": p['owners']['owner1'].get('fullName', 'Private'),
            "last_sale": p['sales'].get('saleSearchDate', 'N/A'),
            "price": f"${p['sales'].get('salePriceAmount', 0):,}",
            "year": p['summary'].get('yearBuilt', 'N/A')
        }
    except Exception as e:
        st.error(f"⚠️ ATTOM Connection Failed: {e}")
        return None

def get_ai(prop_data, address):
    if use_mock: return "9", "Great deal!"
    if not openai_key: return "N/A", "No OpenAI Key"

    try:
        client = openai.OpenAI(api_key=openai_key)
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": f"Score 1-10 and write a pitch for {address} owned by {prop_data['owner']}. Format: SCORE: X | HOOK: Text"}]
        )
        res = resp.choices[0].message.content
        score = res.split('|')[0].replace("SCORE:", "").strip()
        hook = res.split('|')[1].replace("HOOK:", "").strip()
        return score, hook
    except Exception as e:
        st.error(f"❌ OpenAI Error: {e}")
        return "0", "API Error"

# --- 3. THE UI ---

uploaded_file = st.file_uploader("Upload Lead CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    # CLEANING: Remove extra spaces from column names
    df.columns = df.columns.str.strip()
    
    if st.button("🚀 Run Engine"):
        results = []
        for i, row in df.iterrows():
            # Match columns regardless of case
            addr = row.get('Address') or row.get('address')
            cs = row.get('CityState') or row.get('citystate')
            
            if addr and cs:
                data = get_data(addr, cs)
                if data:
                    score, hook = get_ai(data, addr)
                    results.append({
                        "Address": addr,
                        "Owner": data['owner'],
                        "PropIntel Score": score,
                        "Hook": hook
                    })
            else:
                st.warning(f"Row {i} is missing 'Address' or 'CityState' column.")
        
        if results:
            final_df = pd.DataFrame(results)
            st.success("Done!")
            st.dataframe(final_df)
        else:
            st.error("No results found. Check the red error boxes above.")