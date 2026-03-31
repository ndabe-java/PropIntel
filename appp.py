import streamlit as st
import pandas as pd
import openai
import requests
import time

# --- BRANDING ---
st.set_page_config(page_title="PropIntel Engine", page_icon="🏢", layout="wide")
st.title("🏢 PropIntel Engine")
st.markdown("### The High-Velocity Outreach Machine for CRE")

# --- API KEYS ---
openai_key = st.secrets["OPENAI_API_KEY"]
attom_key = st.secrets["ATTOM_API_KEY"]

st.title("🏢 PropIntel Engine")
# --- CORE FUNCTIONS ---

def get_attom_data(address, city_state):
    """Fetches real-time property details from ATTOM API."""
    if not attom_key:
        # Fallback for testing UI without a key
        return {"owner": "Unknown LLC", "last_sale": "2015-01-01", "price": "$0"}

    url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/detail"
    headers = {"apikey": attom_key, "Accept": "application/json"}
    params = {"address1": address, "address2": city_state}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        prop = data['property'][0]
        return {
            "owner": prop['owners']['owner1']['fullName'],
            "last_sale": prop['sales']['saleSearchDate'],
            "price": f"${prop['sales']['salePriceAmount']:,}",
            "year_built": prop['summary']['yearBuilt']
        }
    except Exception as e:
        return None

def generate_propintel_report(owner_data, address):
    """AI Logic: Scores the lead and writes the personalized outreach."""
    if not openai_key:
        return "N/A", "Please provide OpenAI Key."

    client = openai.OpenAI(api_key=openai_key)
    
    prompt = f"""
    You are the PropIntel Engine, a high-end CRE tool. 
    Property: {address}
    Owner: {owner_data['owner']}
    Last Sold: {owner_data['last_sale']} for {owner_data['price']}
    Built: {owner_data['year_built']}

    1. Score this lead (1-10) for 'Likelihood to Sell'. (Higher score if held > 7 years).
    2. Write a 2-sentence 'Hook' for a broker to email this owner. Focus on equity and market timing.
    Format your response as: SCORE: [Number] | HOOK: [Text]
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    res = response.choices[0].message.content
    score = res.split('|')[0].replace("SCORE:", "").strip()
    hook = res.split('|')[1].replace("HOOK:", "").strip()
    return score, hook

# --- INTERFACE ---

uploaded_file = st.file_uploader("Upload CSV (Required columns: Address, CityState)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("Leads Loaded:", len(df))
    
    if st.button("🚀 Run PropIntel Engine"):
        if not openai_key or not attom_key:
            st.error("Missing API Keys in the sidebar!")
        else:
            enriched_data = []
            progress = st.progress(0)
            
            for index, row in df.iterrows():
                # 1. Get real property data
                real_data = get_attom_data(row['Address'], row['CityState'])
                
                if real_data:
                    # 2. Get AI intelligence
                    score, hook = generate_propintel_report(real_data, row['Address'])
                    
                    enriched_data.append({
                        "Address": row['Address'],
                        "Actual Owner": real_data['owner'],
                        "Last Sale": real_data['last_sale'],
                        "Sale Price": real_data['price'],
                        "PropIntel Score": score,
                        "Personalized Hook": hook
                    })
                
                progress.progress((index + 1) / len(df))
                time.sleep(0.5) # Avoid API bans
            
            # 3. Show Results
            results_df = pd.DataFrame(enriched_data)
            st.success("Analysis Complete!")
            st.dataframe(results_df.sort_values(by="PropIntel Score", ascending=False))
            
            # Download for the Broker
            csv = results_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Final Report", data=csv, file_name="propintel_output.csv")