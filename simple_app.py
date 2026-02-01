"""BC Real Estate Investment Analyzer - Simple Test Version."""

import streamlit as st

st.title("🏡 BC Real Estate Investment Analyzer")
st.write("Testing deployment...")

# Test import
try:
    from src.bc_real_estate import get_config
    config = get_config()
    st.success("✅ Successfully imported bc_real_estate package")
    st.write(f"PTT luxury rate: {config.ptt_luxury_rate}")
except Exception as e:
    st.error(f"❌ Import failed: {e}")
