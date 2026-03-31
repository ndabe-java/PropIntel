import streamlit as st

# --- 1. ENTERPRISE INITIALIZATION ---
st.set_page_config(page_title="PropIntel Engine", page_icon="🏢", layout="wide")

st.title("🏢 Welcome to PropIntel Enterprise")
st.markdown("### The Intelligence Layer for Modern CRE Brokers")

# --- 2. SESSION STATE FOR AUTH & SETTINGS ---
if "user_email" not in st.session_state:
    st.session_state.user_email = None

# --- 3. LOGIN GATE ---
if not st.session_state.user_email:
    st.info("Please log in to access the Enterprise Suite.")
    with st.form("login_form"):
        email = st.text_input("Work Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log In")
        
        if submitted and email:
            st.session_state.user_email = email
            st.success("Authenticated! Select a page from the sidebar to begin.")
            st.rerun()
else:
    st.success(f"Welcome back, {st.session_state.user_email}! Use the sidebar to navigate the suite.")
    if st.button("Log Out"):
        st.session_state.user_email = None
        st.rerun()