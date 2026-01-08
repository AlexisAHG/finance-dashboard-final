import streamlit as st
from src.ui.pages_single_asset import render_single_asset_page
from src.ui.pages_portfolio import render_portfolio_page


st.set_page_config(page_title="Finance Dashboard", layout="wide")

st.title("Finance Dashboard")
st.success("Setup OK ✅")

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Choose a module",
    ["Home", "Quant A — Single Asset", "Quant B — Portfolio"]
)

if page == "Home":
    st.write("Welcome to the Finance Dashboard.")
    st.write("Choose a module from the sidebar.")
elif page == "Quant A — Single Asset":
    render_single_asset_page()
elif page == "Quant B — Portfolio":
    render_portfolio_page()




