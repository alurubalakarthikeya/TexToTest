# TexToTest

**TexToTest** is an AI-powered assistant that automatically generates quiz questions from e-learning PDFs using **NLP pipelines**. It combines **Heuristic + Pattern-based approaches** with lightweight NLP and optional semantic validation to create high-quality, domain-relevant quizzes efficiently.

## Features

- **Extract & preprocess content from PDFs**  
  Efficiently extracts text, headings, tables, and key phrases from uploaded PDFs.  

- **Multiple question types**  
  Generates MCQs, Fill-in-the-Blanks, True/False, and Short Answer questions.  

- **Intelligent content selection**  
  Uses heuristics and pattern-based rules to identify key educational concepts.  

- **Answer & distractor generation**  
  Produces high-quality answers and distractors; includes optional lightweight semantic validation for better distractor relevance.  

- **Adaptive self-assessment**  
  Enables scalable quizzes for students, educators, and institutions.  

- **Lightweight & efficient**  
  Works without heavy NLP models for most tasks, making it suitable for local or cloud deployment.

## Tech Stack

- **Frontend:** React.js, CSS, PWA
- **Backend:** Python with FastAPI  
- **AI & NLP:**  
  - HuggingFace Transformers  
  - PEFT (Parameter-Efficient Fine-Tuning)  
  - SpaCy (NER, POS tagging, dependency parsing)  
  - NLTK (tokenization, pattern-based rules)  
  - Sentence-Transformers (lightweight semantic similarity)  
  - PDFPlumber (PDF extraction)  
- **Vector Search:** FAISS for semantic similarity & distractor validation  
- **Hosting:** Render (backend), Vercel (frontend)


## How It Works

1. **Upload PDF**  
   Users upload an e-learning PDF via the frontend.  

2. **Text Extraction & Preprocessing**  
   - PDFPlumber extracts text, tables, and bullet points.  
   - Text is cleaned and chunked for efficient processing.  

3. **Content Selection**  
   - **Heuristic Layer:** Identifies key concepts using NER, POS tagging, frequency analysis, and PDF formatting cues.  
   - **Pattern-based Layer:** Converts key concepts into candidate questions using predefined templates.  

4. **Question & Distractor Generation**  
   - Rule-based pipelines generate question stems.  
   - Distractors are created using spelling/format patterns and optional lightweight semantic similarity checks.  

5. **Result Delivery**  
   - The system returns the generated questions in a clean, responsive UI.  
   - Users can view, download, or export quizzes.

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/alurubalakarthikeya/TexToTest.git
cd TexToTest
```

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload
```

#### Backend configuration

Create a `.env` file in `backend/` with:

```bash
OPENROUTER_API_KEY=sk-or-v1_your_openrouter_key
# Comma-separated list of allowed frontend origins (scheme+host+port)
ALLOWED_ORIGINS=https://your-frontend.example.com,http://localhost:5173
# Optional attribution headers for OpenRouter (recommended but not required)
OPENROUTER_SITE_URL=https://your-frontend.example.com
APP_TITLE=TexToTest
```

Quick diagnostics:

- Check service health: `GET /health`
- Check readiness (context present): `GET /ready`
- Check configuration status: `GET /status`

Example with curl (adjust host/port as needed):

```bash
curl -s http://localhost:8000/status | jq
```

If `openrouter.configured` is false or you get a 401 from `/ask-model`, verify the `OPENROUTER_API_KEY` value in your environment or hosting provider. Keys typically start with `sk-or-v1_…`.

### 3. Frontend Setup

```bash
cd ../frontend
npm install
npm run dev
```

#### Frontend API base

- Set `VITE_API_BASE` in `frontend/.env` to point to your backend (prod or local):

```bash
VITE_API_BASE=https://textotest.onrender.com
# or
# VITE_API_BASE=http://localhost:8000
```

The frontend also falls back to `window.API_BASE` and a sane default if not provided.
