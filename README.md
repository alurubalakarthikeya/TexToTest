# TexToTest

**TexToTest** is an AI-powered assistant that automatically generates quiz questions from e-learning PDFs using **NLP pipelines**. It combines **Heuristic + Pattern-based approaches** with lightweight NLP and optional semantic validation to create high-quality, domain-relevant quizzes efficiently.

## Features

### 📝 **Advanced Question Types**
- **Multiple Choice Questions (MCQ)** - Traditional 4-option questions with intelligent distractors
- **True/False Questions** - Binary choice questions with contextual variations
- **Fill-in-the-Blank** - Interactive completion exercises
- **Short Answer Questions** - Open-ended explanatory responses
- **Matching Questions** - Connect related concepts across columns
- **Mixed Question Sets** - Adaptive combination of question types

### 🧠 **AI-Powered Content Analysis**
- **Intelligent content extraction** from PDFs with advanced text preprocessing
- **Semantic distractor generation** using sentence transformers for contextually relevant wrong answers
- **Automatic difficulty classification** (Easy/Medium/Hard) based on Bloom's taxonomy
- **Subject categorization** into domains like Science, History, Mathematics, Literature, etc.

### 📊 **Professional Export & Integration**
- **Multi-format export**: JSON, Plain Text, PDF, Word Documents, Moodle XML
- **LMS Integration** with Moodle-compatible XML format
- **Professional formatting** with metadata, answer keys, and difficulty indicators
- **Batch processing** for institutional use

### 🎯 **Enhanced User Experience**
- **Interactive question configuration** with type, difficulty, and quantity selection
- **Real-time preview** of different question formats
- **Responsive design** optimized for desktop and mobile
- **Export menu** with format descriptions and compatibility information

### ⚡ **Performance & Reliability**
- **Hybrid NLP pipeline** combining heuristic and ML-based approaches
- **Graceful fallbacks** when advanced features are unavailable
- **Scalable architecture** suitable for individual and institutional deployment
- **Quality validation** with automatic assessment of question and distractor quality

## Tech Stack

- **Frontend:** React.js, CSS, PWA
- **Backend:** Python with FastAPI  
- **AI & NLP:**  
  - Sentence-Transformers (semantic similarity for enhanced distractors)
  - SpaCy (NER, POS tagging, dependency parsing)  
  - NLTK (tokenization, pattern-based rules)  
  - Scikit-learn (ML utilities and classification)
  - NumPy (numerical computations)
  - PDFPlumber (advanced PDF text extraction)  
- **Document Generation:**
  - ReportLab (professional PDF export)
  - python-docx (Word document generation)
  - XML processing (Moodle LMS integration)
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
