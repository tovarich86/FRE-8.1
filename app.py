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

def show_pdf(pdf_content):
    """Exibe o PDF no Streamlit usando PDF.js para evitar bloqueios."""
    base64_pdf = base64.b64encode(pdf_content).decode("utf-8")
    pdf_display = f"""
    <script>
        function openPDF() {{
            var byteCharacters = atob("{base64_pdf}");
            var byteNumbers = new Array(byteCharacters.length);
            for (var i = 0; i < byteCharacters.length; i++) {{
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }}
            var byteArray = new Uint8Array(byteNumbers);
            var blob = new Blob([byteArray], {{type: 'application/pdf'}});
            var url = URL.createObjectURL(blob);
            window.open(url);
        }}
    </script>
    <button onclick="openPDF()">Abrir PDF</button>
    """
    st.components.v1.html(pdf_display, height=50)

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
            st.write("Clique no botão abaixo para visualizar o PDF:")
            show_pdf(pdf_content)
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

# Para hospedagem no GitHub e execução no Streamlit Cloud:
# 1. Salve este arquivo como `app.py`
# 2. Crie um arquivo `requirements.txt` com o seguinte conteúdo:
# streamlit
# pandas
# requests
# beautifulsoup4
# lxml
# 3. Faça upload para um repositório no GitHub
# 4. Vá até https://share.streamlit.io e conecte ao repositório
