import streamlit as st

def aplicar_estilo():

    st.markdown("""
    <style>

    /* Fundo geral */
    .stApp {
        background-color: #f4f6f9;
        font-family: 'Arial';
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
    }

    /* Botões */
    button {
        border-radius: 10px !important;
        font-weight: 600 !important;
    }

    /* Cards padrão Streamlit */
    div[data-testid="stMetric"] {
        background-color: white;
        border-radius: 12px;
        padding: 10px;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.08);
    }

    /* Inputs */
    input, selectbox {
        border-radius: 8px !important;
    }

    </style>
    """, unsafe_allow_html=True)
