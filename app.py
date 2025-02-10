import streamlit as st
import pandas as pd
import re

# URLs dos arquivos CSV e Excel
CSV_URL = "https://github.com/tovarich86/FRE-8.1/raw/main/fre_cia_aberta_2024_otimizado.csv"
EXCEL_URL = "https://github.com/tovarich86/FRE-8.1/raw/main/tabela_consolidada_cvm_otimizado.xlsx"

@st.cache_data
def load_data():
    """Carrega os dados dos arquivos CSV e Excel."""
    df_csv = pd.read_csv(CSV_URL, sep=';', dtype=str, encoding="utf-8")
    df_excel = pd.read_excel(EXCEL_URL, dtype=str)
    
    # Normalizar os nomes das empresas
    def normalize_company_name(name):
        if pd.isna(name):
            return None
        name = name.upper().strip()
        name = re.sub(r"\s+(S\.?A\.?|S/A|SA)$", " S.A.", name)
        return name
    
    df_csv["DENOM_CIA"] = df_csv["DENOM_CIA"].apply(normalize_company_name)
    df_excel["Empresa"] = df_excel["Empresa"].apply(normalize_company_name)
    
    return df_csv, df_excel

df_csv, df_excel = load_data()

# Criar conjuntos das empresas em cada arquivo
empresas_csv = set(df_csv["DENOM_CIA"].dropna())
empresas_excel = set(df_excel["Empresa"].dropna())

# Garantir que todas as empresas do Excel e CSV aparecem na seleção
empresas_unicas = sorted(empresas_csv | empresas_excel)
selected_company = st.selectbox("🏢 Selecione a empresa", empresas_unicas)

# Exibir mensagem caso a empresa não esteja no CSV
if selected_company not in empresas_csv:
    st.warning(f"⚠️ A empresa {selected_company} está no Excel, mas não no CSV.")
