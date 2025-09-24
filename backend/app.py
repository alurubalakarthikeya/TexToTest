from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from model import generate_questions
from utils import extract_text_from_file
from vectordb import store_text, get_context, clear_context
import shutil
import os
from typing import Optional

app = FastAPI(title="TexToTest API", description="Generate multiple-choice questions from uploaded documents")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class QuestionRequest(BaseModel):
    num_questions: Optional[int] = 25
    question_type: Optional[str] = "multiple_choice"  # "multiple_choice" or "simple"

@app.get("/")
def root():
    return {
        "message": "TexToTest Backend is running!",
        "features": [
            "Upload documents (PDF, TXT, MD)",
            "Extract text and store in vector database",
            "Generate multiple-choice questions with distractors",
            "Hybrid heuristic and pattern-based distractor generation"
        ]
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a document and extract text for question generation"""
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        text = extract_text_from_file(file_path)
        if not text:
            raise HTTPException(status_code=400, detail="Could not extract text from file. Supported formats: PDF, TXT, MD")
        
        # Clear previous context and store new text
        clear_context()
        store_text(text)
        
        return {
            "message": "File uploaded and text stored successfully.",
            "filename": file.filename,
            "text_length": len(text),
            "preview": text[:200] + "..." if len(text) > 200 else text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/ask-model")
async def ask_model(request: QuestionRequest = None):
    """Generate questions from uploaded context using OpenRouter Mistral model"""
    if not request:
        request = QuestionRequest()
    
    context = get_context()
    if not context:
        raise HTTPException(status_code=400, detail="No context found. Please upload a file first.")
    
    try:
        questions = generate_questions(
            context, 
            num_questions=request.num_questions,
            question_type=request.question_type
        )
        
        return {
            "questions": questions,
            "total_questions": len(questions),
            "question_type": request.question_type,
            "context_length": len(context)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")

@app.get("/context")
async def get_current_context():
    """Get the current stored context"""
    context = get_context()
    if not context:
        return {"message": "No context stored"}
    
    return {
        "context_length": len(context),
        "preview": context[:500] + "..." if len(context) > 500 else context
    }

@app.delete("/context")
async def clear_stored_context():
    """Clear the stored context"""
    clear_context()
    return {"message": "Context cleared successfully"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "TexToTest Backend"}
