# backend.py
import os
from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from PyPDF2 import PdfReader
import google.generativeai as genai

# --- Configure Google Generative AI ---
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# --- Initialize FastAPI ---
app = FastAPI(title="Legal AI Backend")

# --- Allow CORS for V0.dev frontend ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to frontend URL in production
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- Helper to extract text ---
def extract_text(file: UploadFile):
    if file.filename.lower().endswith(".pdf"):
        reader = PdfReader(file.file)
        return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
    else:
        return file.file.read().decode("utf-8")

# --- Helper to call AI ---
def call_ai(prompt, max_chars=3000):
    resp = model.generate_content(prompt)
    return resp.text[:max_chars]

# --- Key clauses extraction ---
KEYWORDS = ["liability","termination","payment","confidential","indemnification","force majeure"]
def extract_clauses(text):
    sentences = text.split(".")
    return [s.strip() for s in sentences if any(k in s.lower() for k in KEYWORDS)][:12]

# --- API Endpoints ---
@app.post("/summary")
async def generate_summary(file: UploadFile):
    text = extract_text(file)
    prompt = f"Summarize this legal document in plain English:\n{text[:3000]}"
    summary = call_ai(prompt)
    return {"summary": summary}

@app.post("/clauses")
async def key_clauses(file: UploadFile):
    text = extract_text(file)
    clauses = []
    for c in extract_clauses(text):
        explanation = call_ai(f"Explain this clause in simple English:\n{c}")
        risk = call_ai(f"Rate the risk of this clause: {c}\nAnswer with Low/Medium/High.")
        clauses.append({"clause": c, "explanation": explanation, "risk": risk})
    return {"clauses": clauses}

@app.post("/qa")
async def question_answer(file: UploadFile, question: str = Form(...)):
    text = extract_text(file)
    prompt = f"Answer clearly using the document:\n{text[:3000]}\nQuestion: {question}"
    answer = call_ai(prompt)
    return {"answer": answer}

@app.post("/jargon")
async def define_jargon(term: str = Form(...)):
    definition = call_ai(f"Explain in plain English: {term}")
    return {"definition": definition}
