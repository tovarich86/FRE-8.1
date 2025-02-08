import streamlit as st
import pandas as pd
import base64
import requests
import io
from urllib.parse import urlparse, parse_qs
from PyPDF2 import PdfReader
import tempfile
import openai

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
    codigo_quadro = "8120" if item == "8.4" else "8110"  # Ajuste correto do código do quadro
    return f"https://www.rad.cvm.gov.br/ENET/frmExibirArquivoFRE.aspx?NumeroSequencialDocumento={doc_number}&CodigoGrupo=8000&CodigoQuadro={codigo_quadro}&Tipo=&RelatorioRevisaoEspecial=&CodTipoDocumento=9"

def download_pdf(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Referer": "https://www.rad.cvm.gov.br/",
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200 and "application/pdf" in response.headers.get("Content-Type", ""):
        return response.content  # Retorna o binário do PDF diretamente
    else:
        st.error(f"Erro ao acessar a página ({response.status_code}). Verifique se o documento está disponível.")
        return None

def summarize_pdf(pdf_content):
    """Lê o PDF e gera um resumo dos principais pontos usando IA."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        tmpfile.write(pdf_content)
        tmpfile_path = tmpfile.name
    
    reader = PdfReader(tmpfile_path)
    text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    
    if len(text) > 5000:  # Limita o tamanho do texto para evitar cortes
        text = text[:5000]
    
    # Chamada para IA
    openai.api_key = "SUA_API_OPENAI"  # Substitua pela sua chave
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Resuma o seguinte documento destacando os principais pontos:"},
            {"role": "user", "content": text}
        ]
    )
    return response["choices"][0]["message"]["content"]

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
        
        if st.button("Gerar Resumo do Documento"):
            summary = summarize_pdf(pdf_content)
            st.write("### Resumo do Documento:")
            st.write(summary)
    else:
        st.error("Falha ao baixar o documento.")
