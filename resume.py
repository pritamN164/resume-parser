import pdfplumber
import docx
import re
import spacy
import streamlit as st
import pandas as pd
import plotly.express as px
import pytesseract
from PIL import Image

nlp = spacy.load("en_core_web_sm")

# PAGE CONFIG
st.set_page_config(page_title="AI Resume Analyzer", page_icon="🚀", layout="wide")

# ADVANCED UI
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #141E30, #243B55);
}
.title {
    text-align: center;
    font-size: 50px;
    font-weight: bold;
    color: #00FFD1;
}
.card {
    background: rgba(255,255,255,0.1);
    backdrop-filter: blur(10px);
    padding: 25px;
    border-radius: 20px;
    margin-bottom: 20px;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# TEXT EXTRACTION
def read_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted
            else:
                img = page.to_image().original
                text += pytesseract.image_to_string(img)
    return text

def read_docx(file):
    doc = docx.Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

# BASIC EXTRACTION
def extract_email(text):
    match = re.findall(r'\S+@\S+', text)
    return match[0] if match else "Not Found"

def extract_phone(text):
    match = re.findall(r'\+?\d[\d -]{8,12}\d', text)
    return match[0] if match else "Not Found"

def extract_name(text):
    doc = nlp(text[:1000])
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return "Not Found"


# ADVANCED SKILLS
def extract_skills(text):
    skills_db = [
        "python","java","c++","machine learning","deep learning",
        "sql","html","css","javascript","react","node","flask",
        "django","tensorflow","pytorch","data analysis",
        "pandas","numpy","excel","power bi","aws","docker"
    ]

    text = text.lower()
    found = []

    for skill in skills_db:
        if skill in text:
            found.append(skill.title())

    return list(set(found))

# EDUCATION
def extract_education(text):
    degrees = ["b.tech","m.tech","bsc","msc","mba","bachelor","master"]
    text = text.lower()
    return [d.upper() for d in degrees if d in text]

# EXPERIENCE
def extract_experience(text):
    matches = re.findall(r'(\d+)\+?\s+years', text.lower())
    return max(matches) + " years" if matches else "Not Found"

# CERTIFICATIONS
def extract_certifications(text):
    patterns = [
        r'certified\s.*',
        r'certificate\s.*',
        r'coursera\s.*',
        r'udemy\s.*',
        r'aws\s.*',
        r'google\s.*'
    ]

    lines = text.split("\n")
    certs = []

    for line in lines:
        for p in patterns:
            if re.search(p, line.lower()):
                certs.append(line.strip())

    return list(set(certs))[:10]

# MATCH SCORE
def match_score(skills, jd):
    score = 0
    for skill in skills:
        if skill.lower() in jd.lower():
            score += 10
    return min(score, 100)

# PARSER
def parse_resume(file, file_type, jd=""):
    text = read_pdf(file) if file_type == "pdf" else read_docx(file)

    # DEBUG (remove later if you want)
    st.write("🔍 Extracted Text Preview:", text[:500])

    data = {
        "Name": extract_name(text),
        "Email": extract_email(text),
        "Phone": extract_phone(text),
        "Skills": extract_skills(text),
        "Education": extract_education(text),
        "Experience": extract_experience(text),
        "Certifications": extract_certifications(text)
    }

    if jd:
        data["Score"] = match_score(data["Skills"], jd)

    return data

# UI MAIN
def main():
    st.markdown('<div class="title">🚀 AI Resume Analyzer</div>', unsafe_allow_html=True)

    jd = st.text_area("📝 Paste Job Description")

    files = st.file_uploader("📂 Upload Resume(s)", type=["pdf","docx"], accept_multiple_files=True)

    results = []

    if files:
        for file in files:
            file_type = file.name.split(".")[-1]
            res = parse_resume(file, file_type, jd)
            results.append(res)

        for r in results:
            st.markdown('<div class="card">', unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)
            col1.metric("👤 Name", r["Name"])
            col2.metric("📧 Email", r["Email"])
            col3.metric("📞 Phone", r["Phone"])

            st.write("### 💡 Skills")
            st.write(", ".join(r["Skills"]) or "Not Found")

            st.write("### 🎓 Education")
            st.write(", ".join(r["Education"]) or "Not Found")

            st.write("### 💼 Experience")
            st.write(r["Experience"])

            st.write("### 🏅 Certifications")
            if r["Certifications"]:
                for c in r["Certifications"]:
                    st.write("✔️", c)
            else:
                st.write("Not Found")

            if "Score" in r:
                st.progress(r["Score"]/100)
                st.success(f"Match Score: {r['Score']}%")

            st.markdown('</div>', unsafe_allow_html=True)

        # CHART
        if jd:
            df = pd.DataFrame(results)
            fig = px.bar(df, x="Name", y="Score", text="Score",
                         title="Candidate Comparison")
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()