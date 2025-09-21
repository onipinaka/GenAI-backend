# backend.py
import os
import json
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
    allow_origins=["*"],  # ⚠️ replace with frontend URL in production
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- Helper: Extract text ---
def extract_text(file: UploadFile):
    """Extracts text from PDF or TXT file."""
    if file.filename.lower().endswith(".pdf"):
        reader = PdfReader(file.file)
        return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
    return file.file.read().decode("utf-8")

# --- Helper: Call Gemini AI ---
def call_ai(prompt, max_chars=4000):
    """Calls Gemini model with error handling."""
    try:
        resp = model.generate_content(prompt)
        return resp.text[:max_chars] if resp and resp.text else ""
    except Exception as e:
        return f"AI Error: {str(e)}"

# --- API: Document Summary ---
@app.post("/summary")
async def generate_summary(file: UploadFile):
    text = extract_text(file)
    prompt = f"Summarize this legal document in plain English for a non-lawyer:\n{text[:3000]}"
    summary = call_ai(prompt)
    return {"summary": summary.strip()}

# --- API: Key Clauses Extraction ---
@app.post("/clauses")
async def key_clauses(file: UploadFile):
    text = extract_text(file)
    prompt = f"""
    From this legal document, extract up to 10 key clauses related to:
    - liability
    - termination
    - payment
    - confidentiality
    - indemnification
    - force majeure

    For each clause:
    1. Provide the clause text (short).
    2. Explain it in simple English.
    3. Rate the risk as Low, Medium, or High.

    Return output as a JSON array:
    [
      {{
        "clause": "original clause text",
        "explanation": "plain English explanation",
        "risk": "Low/Medium/High"
      }}
    ]

    Document text:
    {text[:3000]}
    """

    raw_output = call_ai(prompt)

    # --- Ensure JSON response ---
    try:
        clauses = json.loads(raw_output)
    except Exception:
        clauses = [{"clause": "Parsing error", "explanation": raw_output, "risk": "Unknown"}]

    return {"clauses": clauses}

# --- API: Question Answering ---
@app.post("/qa")
async def question_answer(file: UploadFile, question: str = Form(...)):
    text = extract_text(file)
    prompt = f"""
    Use the following legal document to answer the question clearly and concisely.
    If the answer is not in the document, say 'Not found in document.'

    Document:
    {text[:3000]}

    Question: {question}
    """
    answer = call_ai(prompt)
    return {"answer": answer.strip()}

# --- API: Jargon Simplification ---
@app.post("/jargon")
async def define_jargon(term: str = Form(...)):
    prompt = f"Explain this legal term in plain English for a non-lawyer: {term}"
    definition = call_ai(prompt)
    return {"definition": definition.strip()}
