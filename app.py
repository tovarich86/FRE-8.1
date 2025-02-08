import streamlit as st
import pandas as pd
import base64
import requests
import io
import tempfile
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

@st.cache_data
def load_data():
    """Carrega o CSV do GitHub e mantém em cache para evitar recarregamentos constantes."""
    url = "https://github.com/tovarich86/FRE-8.1/blob/main/fre_cia_aberta_2024.csv"  # Substitua pela sua URL real
    try:
        df = pd.read_csv(url, sep=';', dtype=str, encoding="latin1", on_bad_lines="skip")
        return df.sort_values(by=["DENOM_CIA", "VERSAO"], ascending=[True, False])
    except Exception as e:
        st.error(f"Erro ao carregar o CSV do GitHub: {e}")
        return pd.DataFrame()

def extract_document_number(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return query_params.get("NumeroSequencialDocumento", [None])[0]

def generate_fre_url(doc_number, item):
    return f"https://www.rad.cvm.gov.br/ENET/frmExibirArquivoFRE.aspx?NumeroSequencialDocumento={doc_number}&CodigoGrupo=8000&CodigoQuadro=8120&Tipo=&RelatorioRevisaoEspecial=&CodTipoDocumento=9&Hash=5YEUulvbdZXe33BVxOH8iNkjFXWVksCC5Ic0zg4LGU"

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

def show_pdf_with_tempfile(pdf_content, company, item):
    """Salva o PDF temporariamente e exibe um link para visualização."""
    filename = f"{company.replace(' ', '_')}_Item_{item}.pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        tmpfile.write(pdf_content)
        tmpfile_path = tmpfile.name
    
    st.write("Visualize o PDF clicando no link abaixo:")
    st.markdown(f"[Clique aqui para abrir o PDF]({tmpfile_path})", unsafe_allow_html=True)

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
    
    if st.button("Visualizar PDF no app"):
        pdf_content = download_pdf(fre_url)
        if pdf_content:
            show_pdf_with_tempfile(pdf_content, selected_company, selected_item)
        else:
            st.error("Falha ao baixar o documento.")

    if st.button("Baixar PDF"):
        pdf_content = download_pdf(fre_url)
        if pdf_content:
            filename = f"{selected_company.replace(' ', '_')}_Item_{selected_item}.pdf"
            st.download_button(
                label="Clique aqui para baixar o PDF",
                data=pdf_content,
                file_name=filename,
                mime="application/pdf"
            )
        else:
            st.error("Falha ao baixar o documento.")
