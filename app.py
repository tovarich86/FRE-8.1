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

# Empresas que estão no CSV, mas não no Excel
diferenca_csv = empresas_csv - empresas_excel
# Empresas que estão no Excel, mas não no CSV
diferenca_excel = empresas_excel - empresas_csv

# Criar DataFrame para exibição
df_diferencas = pd.DataFrame({
    "Empresa": list(diferenca_csv | diferenca_excel),
    "Presente no CSV": [empresa in empresas_csv for empresa in (diferenca_csv | diferenca_excel)],
    "Presente no Excel": [empresa in empresas_excel for empresa in (diferenca_csv | diferenca_excel)]
})

# Exibir os resultados
st.title("📊 Comparação de Empresas entre CSV e Excel")
st.write("Empresas que estão em um dos arquivos, mas não no outro:")
st.dataframe(df_diferencas)

# Garantir que todas as empresas do Excel aparecem na seleção
empresas_unicas = sorted(empresas_csv | empresas_excel)
selected_company = st.selectbox("🏢 Selecione a empresa", empresas_unicas)

# Tratamento de falta de dados para itens 8.1 e 8.4
st.write("\n## 📌 Verificação de Dados para Itens 8.1 e 8.4")

# Criar colunas booleanas para identificar ausência de dados nos itens 8.1 e 8.4
df_csv["Item_8.1_Disponível"] = df_csv["LINK_DOC"].notna()
df_csv["Item_8.4_Disponível"] = df_csv["LINK_DOC"].notna()

df_itens = df_csv[["DENOM_CIA", "Item_8.1_Disponível", "Item_8.4_Disponível"]].drop_duplicates()

st.write("Empresas que possuem ou não informações disponíveis para os itens 8.1 e 8.4:")
st.dataframe(df_itens)

# Exibir mensagem caso a empresa não esteja no CSV
if selected_company not in empresas_csv:
    st.warning(f"⚠️ A empresa {selected_company} está no Excel, mas não no CSV.")
