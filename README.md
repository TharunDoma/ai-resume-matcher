# 🎯 AI Resume Matcher

An AI-powered resume analysis tool that compares your resume against a job description and returns a detailed match score with actionable feedback.

Built as a learning project to practice **Data Engineering (ETL)** concepts using Python, Streamlit, and Google Gemini 2.5 Flash.

---

## 🏗️ Architecture — ETL Pipeline

```
[PDF Resume]
     │
     ▼
 EXTRACT ── pdf_extractor.py      (PyMuPDF reads raw text from PDF)
     │
     ▼
TRANSFORM ── gemini_analyzer.py   (Gemini structures raw text into JSON)
     │
     ▼
 ANALYZE ── job_matcher.py        (Gemini JOINs resume + job description)
     │
     ▼
   LOAD ── app.py                 (Streamlit UI displays results)
```

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.10+ | Core language |
| Streamlit | Web UI (the "Load" layer) |
| PyMuPDF | PDF text extraction (the "Extract" layer) |
| Google Gemini 2.5 Flash | AI transformation + matching engine |
| python-dotenv | Secure API key management |

---

## 🚀 Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/ai-resume-matcher.git
cd ai-resume-matcher
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up your API key
```bash
cp .env.example .env
# Open .env and paste your Gemini API key
```

Get a free Gemini API key at: https://aistudio.google.com/

### 5. Run the app
```bash
streamlit run app.py
```

---

## 📁 Project Structure

```
ai-resume-matcher/
├── app.py                  # Streamlit UI — the Load layer
├── pdf_extractor.py        # PDF text extraction — the Extract layer
├── gemini_analyzer.py      # Resume structuring via Gemini — the Transform layer
├── job_matcher.py          # Resume vs JD matching — the Analyze/JOIN layer
├── test_connection.py      # Gemini API health check
├── requirements.txt        # Project dependencies
├── .env.example            # API key template (safe to commit)
├── .env                    # Your actual API key (NEVER commit this)
└── .gitignore              # Keeps secrets and venv out of Git
```

---

## 🔐 Security

- API keys are stored in `.env` and never committed to version control
- `.env.example` is provided as a safe template for collaborators
- This follows the same pattern used in production cloud environments (AWS Secrets Manager, GCP Secret Manager)

---

## 👨‍💻 Author

**Tharun Doma**  
MS Computer Science — UNC Charlotte  
[tdoma@charlotte.edu](mailto:tdoma@charlotte.edu)
