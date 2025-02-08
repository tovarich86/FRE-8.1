import streamlit as st
import requests
import base64
import pdfplumber
import textwrap
import io
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from transformers import pipeline

# Baixa o modelo de sumarização
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

CSV_URL = "https://github.com/tovarich86/FRE-8.1/raw/refs/heads/main/fre_cia_aberta_2024.csv"

st.title("📄 Visualizador de Documentos FRE - CVM")

def extract_document_number(url):
    """Extrai o número sequencial do documento da URL"""
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
        
        if hidden_input:
            base64_string = hidden_input["value"]
            pdf_bytes = base64.b64decode(base64_string)
            return pdf_bytes
    return None

def extract_text_from_pdf(pdf_content):
    """Extrai texto do PDF com pdfplumber"""
    text = ""
    with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text.strip()

def summarize_text(text):
    """Gera um resumo do texto extraído"""
    if len(text) < 500:
        return "⚠️ O documento não contém informações suficientes para resumo."
    
    text_chunks = [text[i:i+1024] for i in range(0, len(text), 1024)]
    summary = " ".join([summarizer(chunk, max_length=150, min_length=50, do_sample=False)[0]['summary_text'] for chunk in text_chunks])
    return textwrap.fill(summary, width=80)

df = pd.read_csv(CSV_URL, sep=';', dtype=str, encoding="latin1", on_bad_lines="skip")
df = df.sort_values(by=["DENOM_CIA", "VERSAO"], ascending=[True, False])

if not df.empty:
    selected_company = st.selectbox("🏢 Selecione a empresa", df["DENOM_CIA"].unique())
    df_filtered = df[df["DENOM_CIA"] == selected_company]
    latest_version = df_filtered.iloc[0]
    document_url = latest_version["LINK_DOC"]
    document_number = extract_document_number(document_url)

    selected_item = st.radio("📑 Selecione o item", ["8.1", "8.4"])
    fre_url = generate_fre_url(document_number, selected_item)

    st.write(f"### 📄 Documento FRE da {selected_company} - Item {selected_item}")
    st.write(f"[🔗 Clique aqui para acessar o documento]({fre_url})")

    if st.button("⬇️ Baixar PDF"):
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
    
    if st.button("📄 Gerar Resumo do Documento"):
        pdf_content = download_pdf(fre_url)
        if pdf_content:
            extracted_text = extract_text_from_pdf(pdf_content)
            if extracted_text:
                summary = summarize_text(extracted_text)
                st.write("### ✍️ Resumo do Documento:")
                st.write(summary)
            else:
                st.error("❌ O PDF não contém texto extraível.")
        else:
            st.error("❌ Erro ao baixar o documento para resumo.")
