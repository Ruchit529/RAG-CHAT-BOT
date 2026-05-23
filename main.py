import os
import fitz  # PyMuPDF

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

from groq import Groq

# GROQ CLIENT

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)

# =========================
# APP
# =========================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# FILES

DOCS_PATH = "docs"
texts = []

def load_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

for file in os.listdir(DOCS_PATH):

    file_path = os.path.join(DOCS_PATH, file)

    if file.endswith(".txt"):

        with open(file_path, "r", encoding="utf-8") as f:
            texts.append(f.read())

    elif file.endswith(".pdf"):

        pdf_text = load_pdf(file_path)
        texts.append(pdf_text)

print(f"Loaded {len(texts)} documents")

# SPLIT TEXT

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

chunks = []

for t in texts:
    chunks.extend(splitter.split_text(t))

docs = [Document(page_content=c) for c in chunks]

# EMBEDDINGS

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vectorstore = FAISS.from_documents(docs, embedding_model)

retriever = vectorstore.as_retriever(search_kwargs={"k": 5})


# REQUEST MODEL

class Query(BaseModel):
    question: str


# LLM FUNCTION


def call_llm(question: str, context: str):

    prompt = f"""
You are a helpful assistant.

Use ONLY the context below.

Context:
{context}

Question:
{question}

Answer:
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content


# RAG PIPELINE

def generate_answer(question: str):

    docs = retriever.invoke(question)

    context = "\n\n".join([d.page_content for d in docs])

    return call_llm(question, context)


# ROUTES

@app.get("/")
def home():
    return {"message": "RAG with PDF + TXT running"}

@app.post("/ask")
def ask(q: Query):

    answer = generate_answer(q.question)

    return {
        "question": q.question,
        "answer": answer
    }
