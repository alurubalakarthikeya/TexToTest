from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel
from model import generate_questions, get_openrouter_status
from utils import extract_text_from_file
from vectordb import store_text, get_context, clear_context
import shutil
import os
import base64
from io import BytesIO
from typing import Optional, List
from datetime import datetime

# Import new modules with fallback handling
try:
    from content_preprocessor import create_content_preprocessor, extract_text_from_file_advanced
    CONTENT_PREPROCESSOR_AVAILABLE = True
except ImportError:
    CONTENT_PREPROCESSOR_AVAILABLE = False
    print("Warning: Content preprocessor not available")

try:
    from question_validator import create_question_validator
    QUESTION_VALIDATOR_AVAILABLE = True
except ImportError:
    QUESTION_VALIDATOR_AVAILABLE = False
    print("Warning: Question validator not available")

try:
    from quiz_exporter import create_quiz_exporter
    QUIZ_EXPORTER_AVAILABLE = True
except ImportError:
    QUIZ_EXPORTER_AVAILABLE = False
    print("Warning: Quiz exporter not available")

app = FastAPI(title="TexToTest API", description="Generate multiple-choice questions from uploaded documents")

# CORS configuration: allow specific origins via env, default safe wildcard without credentials
_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS = [o.strip() for o in _origins_env.split(",") if o.strip()]
ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "false").lower() == "true"
# If wildcard origins, force credentials off to comply with CORS spec
if any(o == "*" for o in ALLOWED_ORIGINS) and ALLOW_CREDENTIALS:
    ALLOW_CREDENTIALS = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"]
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize advanced modules
content_preprocessor = None
question_validator = None
quiz_exporter = None

if CONTENT_PREPROCESSOR_AVAILABLE:
    try:
        content_preprocessor = create_content_preprocessor()
        print("✅ Content preprocessor initialized")
    except Exception as e:
        print(f"⚠️ Content preprocessor initialization failed: {e}")

if QUESTION_VALIDATOR_AVAILABLE:
    try:
        question_validator = create_question_validator()
        print("✅ Question validator initialized")
    except Exception as e:
        print(f"⚠️ Question validator initialization failed: {e}")
        
if QUIZ_EXPORTER_AVAILABLE:
    try:
        quiz_exporter = create_quiz_exporter()
        print("✅ Quiz exporter initialized")
    except Exception as e:
        print(f"⚠️ Quiz exporter initialization failed: {e}")

class QuestionRequest(BaseModel):
    num_questions: Optional[int] = 25
    question_type: Optional[str] = "multiple_choice"  # "multiple_choice", "true_false", "fill_in_blank", "short_answer", "matching", "mixed", or "simple"
    difficulty: Optional[str] = None  # "easy", "medium", "hard"
    category: Optional[str] = None  # Subject category filter

class ExportRequest(BaseModel):
    questions: List[dict]
    format_type: str  # "pdf", "docx", "json", "xml", "txt"
    title: Optional[str] = "Generated Quiz"
    metadata: Optional[dict] = None

class ValidationRequest(BaseModel):
    questions: List[dict]
    
class ContentAnalysisRequest(BaseModel):
    text: str
    analyze_structure: Optional[bool] = True

@app.get("/")
def root():
    return {
        "message": "TexToTest Enhanced Backend is running!",
        "version": "2.0.0",
        "features": [
            "Multiple Question Types (MCQ, T/F, Fill-in-blank, Short Answer, Matching)",
            "Enhanced Distractor Generation with Semantic Similarity", 
            "Question Difficulty Classification (Easy/Medium/Hard)",
            "Automatic Question Categorization by Subject",
            "Multi-format Export (JSON, CSV, Word, PDF)",
            "Enhanced UI with Interactive Controls",
            "Advanced Content Preprocessing for PDFs",
            "Question Quality Validation with NLP Metrics"
        ],
        "endpoints": {
            "upload": "/upload",
            "generate": "/ask-model", 
            "export": "/export",
            "validate": "/validate-questions",
            "analyze": "/analyze-content",
            "status": "/status",
            "test": "/test"
        },
        "status": "All 8 enhancement features ready!"
    }

@app.get("/test", response_class=HTMLResponse)
async def serve_test_frontend():
    """Serve test frontend for enhanced features"""
    try:
        with open("../test-frontend.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html><head><title>TexToTest API</title></head><body>
        <h1>🚀 TexToTest Enhanced API</h1>
        <p>All 8 enhancement features are ready!</p>
        <p>Test frontend not found. API is available at <a href="/">/</a></p>
        <p>Try uploading via <strong>POST /upload</strong> and generating questions via <strong>POST /ask-model</strong></p>
        </body></html>
        """, status_code=200)

@app.head("/")
def root_head():
    return Response(status_code=200)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a document and extract text for question generation"""
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Try advanced extraction first, fallback to basic
        if content_preprocessor:
            try:
                text = extract_text_from_file_advanced(file_path)
            except Exception as e:
                print(f"Advanced extraction failed: {e}")
                text = extract_text_from_file(file_path)
        else:
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
            question_type=request.question_type,
            difficulty=request.difficulty,
            category=request.category
        )
        
        # Validate questions if validator is available
        validation_results = None
        if question_validator and questions:
            try:
                validation_results = question_validator.validate_quiz_batch(questions)
            except Exception as e:
                print(f"Question validation failed: {e}")
        
        response = {
            "questions": questions,
            "total_questions": len(questions),
            "question_type": request.question_type,
            "difficulty": request.difficulty,
            "category": request.category,
            "context_length": len(context)
        }
        
        if validation_results:
            response["validation"] = {
                "overall_rating": validation_results["overall_quality_rating"],
                "average_score": validation_results["average_scores"]["overall"],
                "issue_count": validation_results["issue_summary"]["total_issues"],
                "recommendations": validation_results["recommendations"][:5]  # Top 5 recommendations
            }
        
        return response
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

@app.head("/health")
async def health_head():
    return Response(status_code=200)

@app.get("/ready")
async def readiness_check():
    """Ready when context exists; useful for platform readiness probes."""
    ctx = get_context()
    return {"ready": bool(ctx), "context_length": len(ctx) if ctx else 0}

@app.get("/status")
async def status():
    """Operational status including OpenRouter config (non-sensitive) and context info."""
    ctx = get_context()
    return {
        "service": "TexToTest Backend",
        "context_ready": bool(ctx),
        "context_length": len(ctx) if ctx else 0,
        "openrouter": get_openrouter_status(),
    }

@app.get("/question-config")
async def get_question_config():
    """Get available question types, difficulties, and categories"""
    return {
        "question_types": [
            {"value": "multiple_choice", "label": "Multiple Choice", "description": "Traditional MCQ with 4 options"},
            {"value": "true_false", "label": "True/False", "description": "Binary true or false questions"},
            {"value": "fill_in_blank", "label": "Fill in the Blank", "description": "Complete the missing word or phrase"},
            {"value": "short_answer", "label": "Short Answer", "description": "Brief explanatory answers"},
            {"value": "matching", "label": "Matching", "description": "Match items from two columns"},
            {"value": "mixed", "label": "Mixed Types", "description": "Combination of different question types"},
            {"value": "simple", "label": "Simple Questions", "description": "Basic text-based questions"}
        ],
        "difficulties": [
            {"value": "easy", "label": "Easy", "description": "Basic recall and understanding"},
            {"value": "medium", "label": "Medium", "description": "Application and analysis"},
            {"value": "hard", "label": "Hard", "description": "Evaluation and synthesis"}
        ],
        "categories": [
            {"value": "science", "label": "Science"},
            {"value": "history", "label": "History"}, 
            {"value": "mathematics", "label": "Mathematics"},
            {"value": "literature", "label": "Literature"},
            {"value": "technology", "label": "Technology"},
            {"value": "business", "label": "Business"},
            {"value": "general", "label": "General"}
        ]
    }

@app.post("/validate-questions")
async def validate_questions(request: ValidationRequest):
    """Validate question quality using NLP metrics and grammar checking"""
    if not question_validator:
        raise HTTPException(status_code=503, detail="Question validation service not available")
    
    try:
        validation_results = question_validator.validate_quiz_batch(request.questions)
        return validation_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@app.post("/export")
async def export_quiz(request: ExportRequest):
    """Export quiz in specified format"""
    if not quiz_exporter:
        raise HTTPException(status_code=503, detail="Export service not available")
    
    try:
        export_result = quiz_exporter.export_quiz(
            questions=request.questions,
            format_type=request.format_type,
            title=request.title,
            metadata=request.metadata
        )
        
        # Handle different response types
        if request.format_type in ['pdf', 'docx']:
            # Return binary content as base64
            return {
                "success": True,
                "filename": export_result["filename"],
                "content": export_result["content"],
                "content_type": export_result["content_type"],
                "encoding": export_result["encoding"]
            }
        else:
            # Return text content directly
            return {
                "success": True,
                "filename": export_result["filename"],
                "content": export_result["content"],
                "content_type": export_result["content_type"]
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/export-formats")
async def get_export_formats():
    """Get available export formats and their capabilities"""
    if not quiz_exporter:
        return {
            "available": False,
            "message": "Export service not available",
            "formats": []
        }
    
    formats = {
        "json": {
            "label": "JSON",
            "description": "Structured data format for developers",
            "available": True,
            "file_extension": ".json"
        },
        "txt": {
            "label": "Plain Text",
            "description": "Human-readable text format",
            "available": True,
            "file_extension": ".txt"
        },
        "xml": {
            "label": "Moodle XML",
            "description": "Learning Management System compatible format",
            "available": True,
            "file_extension": ".xml"
        }
    }
    
    # Check for optional format availability
    if 'docx' in quiz_exporter.supported_formats:
        formats["docx"] = {
            "label": "Word Document",
            "description": "Microsoft Word compatible format",
            "available": True,
            "file_extension": ".docx"
        }
    
    if 'pdf' in quiz_exporter.supported_formats:
        formats["pdf"] = {
            "label": "PDF",
            "description": "Professional formatted document",
            "available": True,
            "file_extension": ".pdf"
        }
    
    return {
        "available": True,
        "supported_formats": quiz_exporter.supported_formats,
        "format_details": formats
    }

@app.post("/analyze-content")
async def analyze_content(request: ContentAnalysisRequest):
    """Analyze text content for educational value and structure"""
    if not content_preprocessor:
        raise HTTPException(status_code=503, detail="Content analysis service not available")
    
    try:
        # Create a temporary text file for analysis
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write(request.text)
            temp_path = temp_file.name
        
        try:
            # Extract content with advanced preprocessing
            extracted_content = content_preprocessor.extract_from_file(temp_path)
            
            analysis_result = {
                "content_quality": extracted_content.quality_score,
                "metadata": extracted_content.metadata,
                "structure": {
                    "headings": extracted_content.headings[:10],  # Limit for response size
                    "key_terms": extracted_content.key_terms[:20],
                    "definitions": extracted_content.definitions[:10],
                    "bullet_points": extracted_content.bullet_points[:15]
                },
                "recommendations": []
            }
            
            # Add recommendations based on analysis
            if extracted_content.quality_score < 0.7:
                analysis_result["recommendations"].append("Consider adding more structured content (headings, definitions)")
            
            if len(extracted_content.headings) < 3:
                analysis_result["recommendations"].append("Add more section headings to improve content organization")
            
            if len(extracted_content.definitions) < 2:
                analysis_result["recommendations"].append("Include more explicit definitions of key terms")
                
            return analysis_result
            
        finally:
            # Clean up temporary file
            os.unlink(temp_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content analysis failed: {str(e)}")

@app.get("/system-status")
async def get_system_status():
    """Get comprehensive system status including all modules"""
    ctx = get_context()
    
    return {
        "service": "TexToTest Backend",
        "version": "2.0.0",
        "context_ready": bool(ctx),
        "context_length": len(ctx) if ctx else 0,
        "modules": {
            "openrouter": get_openrouter_status(),
            "content_preprocessor": {
                "available": CONTENT_PREPROCESSOR_AVAILABLE,
                "initialized": content_preprocessor is not None
            },
            "question_validator": {
                "available": QUESTION_VALIDATOR_AVAILABLE,
                "initialized": question_validator is not None
            },
            "quiz_exporter": {
                "available": QUIZ_EXPORTER_AVAILABLE,
                "initialized": quiz_exporter is not None,
                "supported_formats": quiz_exporter.supported_formats if quiz_exporter else []
            }
        },
        "features": {
            "advanced_pdf_extraction": CONTENT_PREPROCESSOR_AVAILABLE,
            "question_validation": QUESTION_VALIDATOR_AVAILABLE,
            "multi_format_export": QUIZ_EXPORTER_AVAILABLE,
            "semantic_distractors": True,  # From enhanced_distractors.py
            "multiple_question_types": True
        }
    }

@app.post("/export")
async def export_quiz(request: ExportRequest):
    """Export quiz in specified format"""
    try:
        # Initialize exporter
        from quiz_exporter import create_quiz_exporter
        exporter = create_quiz_exporter()
        
        # Check if format is supported
        if request.format_type not in exporter.supported_formats:
            raise HTTPException(
                status_code=400, 
                detail=f"Format '{request.format_type}' not supported. Available: {exporter.supported_formats}"
            )
        
        # Prepare metadata
        metadata = request.metadata or {}
        metadata.update({
            'generated_at': datetime.now().isoformat(),
            'total_questions': len(request.questions),
            'title': request.title
        })
        
        # Export quiz
        export_result = exporter.export_quiz(
            questions=request.questions,
            format_type=request.format_type,
            title=request.title,
            metadata=metadata
        )
        
        # For binary formats (PDF, DOCX), return as download
        if export_result.get('encoding') == 'base64':
            content = base64.b64decode(export_result['content'])
            return StreamingResponse(
                BytesIO(content),
                media_type=export_result['content_type'],
                headers={"Content-Disposition": f"attachment; filename={export_result['filename']}"}
            )
        
        # For text formats, return content directly
        return {
            "content": export_result['content'],
            "content_type": export_result['content_type'],
            "filename": export_result['filename'],
            "message": f"Quiz exported successfully as {request.format_type.upper()}"
        }
        
    except ImportError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Export format '{request.format_type}' requires additional dependencies: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/export-formats")
async def get_export_formats():
    """Get available export formats with their capabilities"""
    try:
        from quiz_exporter import create_quiz_exporter
        exporter = create_quiz_exporter()
        
        format_info = {
            'json': {
                'label': 'JSON',
                'description': 'Structured data format for developers',
                'file_extension': '.json',
                'available': 'json' in exporter.supported_formats
            },
            'txt': {
                'label': 'Plain Text',
                'description': 'Simple text format, human-readable',
                'file_extension': '.txt',
                'available': 'txt' in exporter.supported_formats
            },
            'xml': {
                'label': 'Moodle XML',
                'description': 'Moodle LMS compatible format',
                'file_extension': '.xml',
                'available': 'xml' in exporter.supported_formats
            },
            'pdf': {
                'label': 'PDF Document',
                'description': 'Professional formatted document',
                'file_extension': '.pdf',
                'available': 'pdf' in exporter.supported_formats
            },
            'docx': {
                'label': 'Word Document',
                'description': 'Microsoft Word compatible format',
                'file_extension': '.docx',
                'available': 'docx' in exporter.supported_formats
            }
        }
        
        return {
            "supported_formats": exporter.supported_formats,
            "format_details": format_info,
            "total_available": len(exporter.supported_formats)
        }
        
    except ImportError:
        return {
            "supported_formats": ['json', 'txt', 'xml'],
            "format_details": {
                "json": {"label": "JSON", "available": True},
                "txt": {"label": "Plain Text", "available": True},
                "xml": {"label": "Moodle XML", "available": True},
                "pdf": {"label": "PDF Document", "available": False, "reason": "reportlab not installed"},
                "docx": {"label": "Word Document", "available": False, "reason": "python-docx not installed"}
            },
            "total_available": 3
        }
