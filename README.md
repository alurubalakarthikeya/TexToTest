<h2 align="center">TexToTest</h2>

**TexToTest** is an AI-powered assistant that automatically generates quiz questions from **e-learning PDFs** using NLP pipelines.  

It helps educators, students, and institutions by:  

- Extracting and preprocessing content from PDFs  
- Generating multiple types of quiz questions (MCQs, Fill-in-the-Blanks, True/False, Short Answer)  
- Selecting key educational concepts intelligently  
- Producing high-quality answers and distractors  
- Enabling adaptive and scalable self-assessment for learners  

## Tech Stack

- **Frontend**: React.js, CSS  
- **Backend**: Python with FastAPI 
- **AI & NLP**: HuggingFace Transformers, PEFT, SpaCy, NLTK, Sentence-Transformers, PDFPlumber 
- **Vector Search**: FAISS for semantic similarity 
- **Question Generation Model**: Fine-tuned pythia-410m
- **Hosting**: Render, Vercel 

## How It Works

1. **User uploads an e-learning PDF**  
2. **Text extraction & preprocessing** (using PDFPlumber)  
3. **Content selection** via summarization, embeddings, and key concept extraction  
4. **Question generation** using rule-based + neural NLP pipelines  
5. **Answer & distractor generation** (for MCQs and cloze questions)  
6. **Result returned** to the user in a clean, responsive UI  

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/TexToTest.git
cd TexToTest
```

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload
```

### 3. Frontend Setup

```bash
cd ../frontend
npm install
npm run dev
```

