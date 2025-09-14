from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow frontend (React) to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # set to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    # For now, mock response (later process PDF with NLP)
    questions = [
        {
            "q": "What is the capital of France?",
            "options": ["Berlin", "Madrid", "London", "Paris"],
        },
        {
            "q": "Which language is primarily used for styling web pages?",
            "options": ["Python", "HTML", "CSS", "C++"],
        },
    ]
    return {"questions": questions}
