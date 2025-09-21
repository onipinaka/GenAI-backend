# app.py
import os, textwrap, re
import streamlit as st
from PyPDF2 import PdfReader
import google.generativeai as genai

# --- Google Generative AI Setup ---
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-pro")

# --- Helper function ---
def call_ai(prompt, max_chars=3000):
    resp = model.generate_content(prompt)
    return textwrap.shorten(resp.text, width=max_chars, placeholder="...")

# --- Extract text from PDF/TXT ---
def extract_text(file):
    if file.name.lower().endswith(".pdf"):
        reader = PdfReader(file)
        return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
    else:
        return file.getvalue().decode("utf-8")

# --- Identify key clauses ---
KEYWORDS = ["liability","termination","payment","confidential","indemnification","force majeure"]
def extract_clauses(text):
    sentences = re.split(r'(?<=[.\n])\s+', text)
    return [s.strip() for s in sentences if any(k in s.lower() for k in KEYWORDS)][:12]

# --- Streamlit UI ---
st.title("Legal Document AI Assistant")

uploaded_file = st.file_uploader("Upload PDF/TXT")
if uploaded_file:
    raw_text = extract_text(uploaded_file)
    st.subheader("Document Preview (first 500 chars)")
    st.code(raw_text[:500]+"..." if len(raw_text)>500 else raw_text)

    # 1) Summary
    if st.button("Generate Summary"):
        prompt = f"Summarize this legal document in plain English:\n{raw_text[:3000]}"
        summary = call_ai(prompt)
        st.markdown("**Summary:**")
        st.write(summary)

    # 2) Key Clauses
    if st.button("Identify Key Clauses"):
        clauses = extract_clauses(raw_text)
        for i,c in enumerate(clauses):
            with st.expander(f"Clause {i+1}: {c[:60]}..."):
                explanation = call_ai(f"Explain in simple English:\n{c}")
                risk_prompt = f"Rate the risk of this clause: {c}\nAnswer with Low/Medium/High."
                risk = call_ai(risk_prompt, max_chars=200)
                color = "red" if "High" in risk else "orange" if "Medium" in risk else "green"
                st.markdown(f"<span style='color:{color}'>{risk}</span>", unsafe_allow_html=True)
                st.write(explanation)

    # 3) Q&A
    question = st.text_input("Ask a question about this document:")
    if question:
        prompt = f"Answer clearly using the document:\n{raw_text[:3000]}\nQuestion: {question}"
        answer = call_ai(prompt)
        st.markdown("**Answer:**")
        st.write(answer)

    # 4) Jargon
    jargon_input = st.text_input("Enter a legal term to define:")
    if jargon_input:
        prompt = f"Explain in plain English: {jargon_input}"
        definition = call_ai(prompt)
        st.markdown(f"**Definition of {jargon_input}:**")
        st.write(definition)

st.caption("Prototype — not legal advice. Consult a lawyer for official guidance.")
