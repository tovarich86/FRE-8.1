import streamlit as st
import pandas as pd
import base64
from urllib.parse import urlparse, parse_qs

def load_data():
    url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/DADOS/fre_cia_aberta_2024.zip"
    df = pd.read_csv(url, sep=';', dtype=str)
    return df

def extract_document_number(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return query_params.get("NumeroSequencialDocumento", [None])[0]

def generate_fre_url(doc_number, item):
    return f"https://www.rad.cvm.gov.br/ENET/frmExibirArquivoFRE.aspx?NumeroSequencialDocumento={doc_number}&CodigoGrupo=8000&CodigoQuadro=8120&Tipo=&RelatorioRevisaoEspecial=&CodTipoDocumento=9&Hash=5YEUulvbdZXe33BVxOH8iNkjFXWVksCC5Ic0zg4LGU"

st.title("Visualizador de Documentos FRE - CVM")
df = load_data()

df = df.sort_values(by=["DENOM_CIA", "VERSAO"], ascending=[True, False])
selected_company = st.selectbox("Selecione a empresa", df["DENOM_CIA"].unique())

df_filtered = df[df["DENOM_CIA"] == selected_company]
latest_version = df_filtered.iloc[0]
document_url = latest_version["LINK_DOC"]
document_number = extract_document_number(document_url)

selected_item = st.radio("Selecione o item", ["8.1", "8.4"])
fre_url = generate_fre_url(document_number, selected_item)

st.write(f"### Documento FRE da {selected_company} - Item {selected_item}")
st.write(f"[Clique aqui para acessar o documento]({fre_url})")
