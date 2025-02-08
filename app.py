import streamlit as st
import pandas as pd
import base64
import requests
import io
import spacy
import textwrap
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from PyPDF2 import PdfReader
import tempfile

# Baixa automaticamente o modelo spaCy para português
try:
    nlp = spacy.load("pt_core_news_sm")
except:
    st.error("Erro ao carregar o modelo de NLP. Execute: python -m spacy download pt_core_news_sm")
    st.stop()

CSV_URL = "https://github.com/tovarich86/FRE-8.1/raw/refs/heads/main/fre_cia_aberta_2024.csv"

st.title("📄 Visualizador de Documentos FRE - CVM")

def load_data():
    """Carrega os dados CSV diretamente do repositório GitHub"""
    response = requests.get(CSV_URL)
    if response.status_code == 200:
        try:
            df = pd.read_csv(io.StringIO(response.text), sep=';', dtype=str, encoding="latin1", on_bad_lines="skip")
            st.success("✅ Dados carregados com sucesso!")
            return df.sort_values(by=["DENOM_CIA", "VERSAO"], ascending=[True, False])
        except Exception as e:
            st.error(f"❌ Erro ao carregar CSV: {e}")
            return pd.DataFrame()
    else:
        st.error("❌ Erro ao baixar os dados da CVM")
        return pd.DataFrame()

def extract_document_number(url):
    """Extrai o número sequencial do documento a partir da URL"""
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return query_params.get("NumeroSequencialDocumento", [None])[0]

def generate_fre_url(doc_number, item):
    """Gera a URL do documento FRE no site da CVM"""
    codigo_quadro = "8120" if item == "8.4" else "8030"
    return f"https://www.rad.cvm.gov.br/ENET/frmExibirArquivoFRE.aspx?NumeroSequencialDocumento={doc_number}&CodigoGrupo=8000&CodigoQuadro={codigo_quadro}&Tipo=&RelatorioRevisaoEspecial=&CodTipoDocumento=9"

def download_pdf(url):
    """Baixa o PDF codificado em Base64 do site da CVM"""
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

def summarize_pdf(pdf_content):
    """Lê o PDF e gera um resumo eficiente usando spaCy"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        tmpfile.write(pdf_content)
        tmpfile_path = tmpfile.name

    reader = PdfReader(tmpfile_path)
    text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])

    if not text.strip():
        return "⚠️ O documento não contém texto extraível. Pode ser um PDF escaneado."

    try:
        # Processa o texto com spaCy
        doc = nlp(text)

        # Extrai as frases mais importantes (simplesmente pegando as primeiras 10 frases)
        sentences = [sent.text for sent in doc.sents]
        summary = " ".join(sentences[:10])

        # Formata o resumo para melhor visualização
        wrapped_summary = textwrap.fill(summary, width=80)
        return wrapped_summary

    except Exception as e:
        return f"❌ Erro ao processar o PDF: {e}"

df = load_data()

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

    if st.button("⬇️ Gerar link para download PDF"):
        pdf_content = download_pdf(fre_url)
        if pdf_content:
            filename = f"{selected_company.replace(' ', '_')}_Item_{selected_item}.pdf"
            st.download_button(
                label="📥 Clique aqui para baixar o PDF",
                data=pdf_content,
                file_name=filename,
                mime="application/pdf"
            )
        else:
            st.error("❌ Falha ao baixar o documento.")
    
    if st.button("📄 Gerar Resumo do Documento"):
        pdf_content = download_pdf(fre_url)
        if pdf_content:
            summary = summarize_pdf(pdf_content)
            if summary:
                st.write("### ✍️ Resumo do Documento:")
                st.write(summary)
        else:
            st.error("❌ Erro ao baixar o documento para resumo. Verifique se ele está disponível.")
