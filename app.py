import streamlit as st
from src.ui.pages_single_asset import render_single_asset_page

st.set_page_config(page_title="Finance Dashboard", layout="wide")

st.title("Finance Dashboard")
st.success("Setup OK ✅")

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Choisir un module",
    ["Home", "Quant A — Single Asset"]
)

if page == "Home":
    st.write("Bienvenue sur le Finance Dashboard.")
    st.write("Choisis un module dans la barre de gauche.")
else:
    render_single_asset_page()



