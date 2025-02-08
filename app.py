import streamlit as st
import pandas as pd
import base64
import requests
import zipfile
import io
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

CSV_URL = "https://github.com/tovarich86/FRE-8.1/raw/refs/heads/main/fre_cia_aberta_2024.csv"  # Substitua pelo link correto

@st.cache_data
def load_data():
    """Carrega o CSV do GitHub e mantém em cache para evitar recarregamentos constantes."""
    try:
        df = pd.read_csv(CSV_URL, sep=';', dtype=str, encoding="latin1", on_bad_lines="skip")
        return df.sort_values(by=["DENOM_CIA", "VERSAO"], ascending=[True, False])
    except Exception as e:
        st.error(f"Erro ao carregar o CSV do GitHub: {e}")
        return pd.DataFrame()

def extract_document_number(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return query_params.get("NumeroSequencialDocumento", [None])[0]

def generate_fre_url(doc_number, item):
    codigo_quadro = "8120" if item == "8.4" else "8030"  # Ajuste correto do código do quadro
    return f"https://www.rad.cvm.gov.br/ENET/frmExibirArquivoFRE.aspx?NumeroSequencialDocumento={doc_number}&CodigoGrupo=8000&CodigoQuadro={codigo_quadro}&Tipo=&RelatorioRevisaoEspecial=&CodTipoDocumento=9&Hash=5YEUulvbdZXe33BVxOH8iNkjFXWVksCC5Ic0zg4LGU"

def download_pdf(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        hidden_input = soup.find("input", {"id": "hdnConteudoArquivo"})
        
        if hidden_input:
            base64_string = hidden_input["value"]
            pdf_bytes = base64.b64decode(base64_string)
            return pdf_bytes
    return None

df = load_data()
st.title("Visualizador de Documentos FRE - CVM")

if not df.empty:
    selected_company = st.selectbox("Selecione a empresa", df["DENOM_CIA"].unique())
    df_filtered = df[df["DENOM_CIA"] == selected_company]
    latest_version = df_filtered.iloc[0]
    document_url = latest_version["LINK_DOC"]
    document_number = extract_document_number(document_url)

    selected_item = st.radio("Selecione o item", ["8.1", "8.4"])
    fre_url = generate_fre_url(document_number, selected_item)

    st.write(f"### Documento FRE da {selected_company} - Item {selected_item}")
    
    st.markdown(
        f'<a href="{fre_url}" target="_blank" onclick="window.open(this.href,\'_blank\',\'toolbar=0,scrollbars=0,resizable=1\'); return false;">'
        f'<button style="width:100%; padding: 15px; font-size: 16px;">Clique aqui para visualizar o PDF</button>'
        '</a>',
        unsafe_allow_html=True
    )

    pdf_content = download_pdf(fre_url)
    if pdf_content:
        filename = f"{selected_company.replace(' ', '_')}_Item_{selected_item}.pdf"
        st.download_button(
            label="Baixar PDF",
            data=pdf_content,
            file_name=filename,
            mime="application/pdf"
        )
    else:
        st.error("Falha ao baixar o documento.")
