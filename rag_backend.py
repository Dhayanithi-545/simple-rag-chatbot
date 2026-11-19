import os
import chromadb
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

load_dotenv()

embedder = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_or_create_collection("pdf_docs")


def process_pdf(file_path):
    reader = PdfReader(file_path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    chunks = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_text(text)

    if not chunks:
        return

    embeddings = embedder.embed_documents(chunks)
    ids = [f"{os.path.basename(file_path)}_{i}" for i in range(len(chunks))]
    collection.upsert(ids=ids, documents=chunks, embeddings=embeddings)


def ask_question(query):
    if collection.count() == 0:
        return "Please upload and process a PDF first."

    query_embedding = embedder.embed_query(query)
    results = collection.query(query_embeddings=[query_embedding], n_results=3)
    context = "\n\n".join(results["documents"][0])

    prompt = f"Answer using only the context below:\n\n{context}\n\nQuestion: {query}"
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    return llm.invoke(prompt).content