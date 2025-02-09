import streamlit as st
import requests
import base64
import pdfplumber
import io
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import pandas as pd

# URL do CSV contendo os documentos FRE
CSV_URL = "https://github.com/tovarich86/FRE-8.1/raw/refs/heads/main/fre_cia_aberta_2024.csv"

st.title("📄 Visualizador de Documentos FRE - CVM")

@st.cache_data
def load_data():
    """Carrega e processa o CSV com os dados das empresas"""
    try:
        df = pd.read_csv(CSV_URL, sep=';', dtype=str, encoding="latin1", on_bad_lines="skip")
        df = df.sort_values(by=["DENOM_CIA", "VERSAO"], ascending=[True, False])
        return df
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return pd.DataFrame()

df = load_data()

def extract_document_number(url):
    """Extrai o número sequencial do documento da URL"""
    if pd.isna(url):
        return None
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return query_params.get("NumeroSequencialDocumento", [None])[0]

def generate_fre_url(doc_number, item):
    """Gera a URL do documento FRE"""
    codigo_quadro = "8120" if item == "8.4" else "8030"
    return f"https://www.rad.cvm.gov.br/ENET/frmExibirArquivoFRE.aspx?NumeroSequencialDocumento={doc_number}&CodigoGrupo=8000&CodigoQuadro={codigo_quadro}"

def download_pdf(url):
    """Baixa o PDF em Base64 do site da CVM"""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        hidden_input = soup.find("input", {"id": "hdnConteudoArquivo"})
        
        if hidden_input and hidden_input.get("value"):
            try:
                base64_string = hidden_input["value"]
                pdf_bytes = base64.b64decode(base64_string)
                return pdf_bytes
            except Exception as e:
                st.error(f"Erro ao decodificar o PDF: {e}")
    return None

if not df.empty:
    selected_company = st.selectbox("🏢 Selecione a empresa", df["DENOM_CIA"].unique())

    df_filtered = df[df["DENOM_CIA"] == selected_company]
    
    # Exibir tabela com versões disponíveis
    st.write("📊 **Versões disponíveis:**")
    st.dataframe(df_filtered[["VERSAO", "DT_REFER", "DT_ENVIO", "LINK_DOC"]])

    latest_version = df_filtered.iloc[0]
    document_url = latest_version["LINK_DOC"]
    document_number = extract_document_number(document_url)

    if document_number:
        selected_item = st.radio("📑 Selecione o item", ["8.1", "8.4"])
        fre_url = generate_fre_url(document_number, selected_item)

        st.write(f"### 📄 Documento FRE da {selected_company} - Item {selected_item}")
        st.write(f"[🔗 Abrir documento em uma nova aba]({fre_url})")

        if st.button("⬇️ Gerar link para download PDF"):
            with st.spinner("Baixando documento..."):
                pdf_content = download_pdf(fre_url)
            if pdf_content:
                filename = f"{selected_company.replace(' ', '_')}_Item_{selected_item}.pdf"
                st.download_button(
                    label="📥 Baixar PDF",
                    data=pdf_content,
                    file_name=filename,
                    mime="application/pdf"
                )
            else:
                st.error("❌ Falha ao baixar o documento.")
    else:
        st.warning("⚠️ Documento não encontrado para esta empresa.")
