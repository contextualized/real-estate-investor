"""BC Real Estate Investment Analyzer - Main Entry Point.

This is a wrapper that loads the actual Streamlit app from streamlit_app/app.py.
Required for Streamlit Community Cloud deployment.
"""

import sys
from pathlib import Path

# Add streamlit_app to Python path
streamlit_app_dir = Path(__file__).parent / "streamlit_app"
sys.path.insert(0, str(streamlit_app_dir))

# Import and run the actual app
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="BC Real Estate Investment Analyzer",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Main title
st.title("🏡 BC Real Estate Investment Analyzer")
st.markdown(
    """
    Analyze British Columbia property investments with comprehensive calculations for:
    - Buyer acquisition costs (PTT, closing costs, monthly carry)
    - Seller exit proceeds (commission, capital gains)
    - Investment returns (ROCI, IRR)
    """
)

# Sidebar
with st.sidebar:
    st.header("Configuration")
    st.markdown(
        """
        **BC 2026 Tax Rates**

        **Key Rates:**
        - PTT: 1% on first $200k, 2% to $2M, 3% to $3M, 5% above
        - First-Time Buyer Exemption: Up to $500k
        - Newly Built Exemption: Up to $1.1M
        - Realtor Commission: 7% on first $100k, 2.5% remainder
        - Capital Gains Inclusion: 50% (default) or 66.67%
        """
    )

# Create tabs
tab1, tab2, tab3 = st.tabs([
    "💰 Buyer Assessment",
    "📈 Seller Forecast",
    "📊 Scenario Comparison"
])

# Import and render tab pages
with tab1:
    from pages import buyer_assessment as buyer_page
    buyer_page.render()

with tab2:
    from pages import seller_forecast as seller_page
    seller_page.render()

with tab3:
    from pages import scenario_comparison as comparison_page
    comparison_page.render()
