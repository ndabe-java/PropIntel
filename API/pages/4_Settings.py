import streamlit as st

st.set_page_config(page_title="Settings | PropIntel", layout="wide")

if not st.session_state.get("user_email"):
    st.warning("Please log in from the main page.")
    st.stop()

st.title("⚙️ Account & Settings")

# --- 1. BILLING & STRIPE INTEGRATION ---
st.subheader("💳 Subscription & Billing")
st.markdown("""
<div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
    <h3>Current Plan: <span style='color: #007BFF;'>Free Tier</span></h3>
    <ul>
        <li>Bring Your Own Keys (BYOK)</li>
        <li>Max 50 leads per upload</li>
        <li>Standard Support</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Replace this URL with your actual Stripe Payment Link
stripe_checkout_url = "https://buy.stripe.com/test_123456789"
st.link_button("🚀 Upgrade to Enterprise ($99/mo) via Stripe", stripe_checkout_url, type="primary")

st.divider()

# --- 2. BRING YOUR OWN KEY (BYOK) MANAGEMENT ---
st.subheader("🔑 API Key Management")
st.write("Securely store your API keys for processing. These are saved to your active session.")

with st.form("api_keys_form"):
    current_groq = st.session_state.get("groq_key", "")
    current_attom = st.session_state.get("attom_key", "")
    
    groq_input = st.text_input("Groq API Key", value=current_groq, type="password")
    attom_input = st.text_input("ATTOM API Key", value=current_attom, type="password")
    
    if st.form_submit_button("Save Keys"):
        st.session_state.groq_key = groq_input
        st.session_state.attom_key = attom_input
        st.success("API Keys securely updated for this session.")

st.divider()
st.subheader("Danger Zone")
if st.button("Delete Account Data"):
    st.error("This action will contact the database admin to wipe your CRM records.")