import streamlit as st
import pandas as pd
import openai
import requests
import time

# --- 1. SETTINGS & BRANDING ---
st.set_page_config(page_title="PropIntel Engine", page_icon="🏢", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; background-color: #007BFF; color: white; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏢 PropIntel Engine")
st.caption("Commercial Real Estate Intelligence & Outreach Automation")

# --- 2. API KEY MANAGEMENT ---
# Priority: 1. Streamlit Secrets (Cloud) -> 2. Sidebar Input (Manual)
with st.sidebar:
    st.header("🔑 Connection Settings")
    
    # Try to get keys from Secrets (for GitHub/Cloud deployment)
    try:
        default_openai = st.secrets["OPENAI_API_KEY"]
        default_attom = st.secrets["ATTOM_API_KEY"]
    except:
        default_openai = ""
        default_attom = ""

    openai_key = st.text_input("OpenAI API Key", value=default_openai, type="password")
    attom_key = st.text_input("ATTOM API Key", value=default_attom, type="password")
    
    st.divider()
    use_mock = st.checkbox("Use Mock Data (Test Mode)", value=False)
    st.info("Mock Mode allows you to test the UI without spending API credits.")

# --- 3. CORE LOGIC FUNCTIONS ---

def get_property_data(address, city_state):
    """Fetches ownership data from ATTOM API."""
    if use_mock or not attom_key:
        return {"owner": "PropIntel Holdings LLC", "last_sale": "2016-04-12", "price": "$4,250,000", "year_built": "1998"}

    url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/detail"
    headers = {"apikey": attom_key, "Accept": "application/json"}
    params = {"address1": address, "address2": city_state}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        p = data['property'][0]
        return {
            "owner": p['owners']['owner1'].get('fullName', 'Private Owner'),
            "last_sale": p['sales'].get('saleSearchDate', 'Unknown'),
            "price": f"${p['sales'].get('salePriceAmount', 0):,}",
            "year_built": p['summary'].get('yearBuilt', 'N/A')
        }
    except:
        return None

def generate_ai_analysis(prop_data, address):
    """Generates the score and the pitch using OpenAI."""
    if use_mock or not openai_key:
        return "8", "I noticed you've held the asset at " + address + " for several years. Given the current market shift, are you looking to hold or exit?"

    try:
        client = openai.OpenAI(api_key=openai_key)
        prompt = f"""
        Property: {address} | Owner: {prop_data['owner']} | Last Sold: {prop_data['last_sale']}
        1. Score likelihood to sell 1-10 (High score if held > 7 years).
        2. Write a 2-sentence email hook for a broker.
        Return ONLY: SCORE: [X] | HOOK: [Text]
        """
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.choices[0].message.content
        score = text.split('|')[0].replace("SCORE:", "").strip()
        hook = text.split('|')[1].replace("HOOK:", "").strip()
        return score, hook
    except:
        return "5", "Standard Outreach: Interested in discussing your property's valuation?"

# --- 4. THE USER INTERFACE ---

uploaded_file = st.file_uploader("Upload Lead CSV (Columns: Address, CityState)", type=["csv"])

if uploaded_file:
    input_df = pd.read_csv(uploaded_file)
    
    # Verify Columns
    required = ['Address', 'CityState']
    if not all(col in input_df.columns for col in required):
        st.error(f"CSV must contain these exact headers: {required}")
    else:
        st.write(f"✅ Found {len(input_df)} leads. Ready to process.")
        
        if st.button("🚀 Execute Intelligence Engine"):
            enriched_results = []
            progress_bar = st.progress(0)
            
            for i, row in input_df.iterrows():
                # 1. Fetch Data
                p_data = get_property_data(row['Address'], row['CityState'])
                
                if p_data:
                    # 2. Analyze
                    score, hook = generate_ai_analysis(p_data, row['Address'])
                    
                    # 3. Store
                    enriched_results.append({
                        "Address": row['Address'],
                        "City/State": row['CityState'],
                        "Actual Owner": p_data['owner'],
                        "Last Sale": p_data['last_sale'],
                        "PropIntel Score": score,
                        "AI Hook": hook
                    })
                
                progress_bar.progress((i + 1) / len(input_df))
                time.sleep(0.2)

            # --- 5. DATA DISPLAY & DOWNLOAD ---
            if enriched_results:
                final_df = pd.DataFrame(enriched_results)
                
                # The "Error Proof" Sort
                if "PropIntel Score" in final_df.columns:
                    final_df["PropIntel Score"] = pd.to_numeric(final_df["PropIntel Score"], errors='coerce').fillna(0)
                    final_df = final_df.sort_values(by="PropIntel Score", ascending=False)

                st.success("Analysis Complete!")
                st.dataframe(final_df, use_container_width=True)
                
                csv_data = final_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Broker Report", data=csv_data, file_name="propintel_results.csv")
            else:
                st.warning("No data could be processed. Check your API keys or CSV format.")