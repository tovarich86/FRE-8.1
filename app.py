import streamlit as st
import pandas as pd
import base64
import requests
import zipfile
import io
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

def load_data():
    url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/DADOS/fre_cia_aberta_2024.zip"
    
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        
        csv_filename = [name for name in zip_file.namelist() if name.endswith(".csv")][0]
        
        with zip_file.open(csv_filename) as file:
            try:
                df = pd.read_csv(file, sep=';', dtype=str, encoding="latin1", on_bad_lines="skip")
                st.success("Dados carregados com sucesso!")
            except Exception as e:
                st.error(f"Erro ao carregar CSV: {e}")
                return pd.DataFrame()
        
        return df
    else:
        st.error("Erro ao baixar os dados da CVM")
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

def show_pdf_inline(pdf_content):
    """Exibe o PDF inline no próprio Streamlit usando um iframe Base64."""
    base64_pdf = base64.b64encode(pdf_content).decode("utf-8")
    pdf_display = f"""
    <iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800px"></iframe>
    """
    st.markdown(pdf_display, unsafe_allow_html=True)

st.title("Visualizador de Documentos FRE - CVM")
df = load_data()

if not df.empty:
    df = df.sort_values(by=["DENOM_CIA", "VERSAO"], ascending=[True, False])
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
            st.write("Pré-visualização do PDF:")
            show_pdf_inline(pdf_content)
        else:
            st.error("Falha ao baixar o documento.")

    if st.button("Baixar PDF"):
        pdf_content = download_pdf(fre_url)
        if pdf_content:
            st.download_button(
                label="Clique aqui para baixar o PDF",
                data=pdf_content,
                file_name="documento_cvm.pdf",
                mime="application/pdf"
            )
        else:
            st.error("Falha ao baixar o documento.")
