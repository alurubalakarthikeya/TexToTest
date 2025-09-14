from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from model import generate_text

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:3000"] for stricter security
    allow_credentials=True,
    allow_methods=["*"],   # Allow POST, GET, OPTIONS etc.
    allow_headers=["*"],   # Allow headers like Content-Type, Authorization
)


class PromptRequest(BaseModel):
    prompt: str

@app.get("/")
def root():
    return {"message": "Backend is running!"}

@app.post("/ask-model/")
def ask_model(request: PromptRequest):
    output = generate_text(request.prompt)
    return {"response": output}

# ✅ File upload test endpoint
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    return {"questions": [f"Received file: {file.filename}"]}
