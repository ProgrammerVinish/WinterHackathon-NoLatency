from dotenv import load_dotenv
load_dotenv()
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

# Import your existing modules
from analyzer import PythonStaticAnalyzer
from gemini_explainer import GeminiExplainer
app = FastAPI(title="ExplainIt Backend")

# Enable CORS (allows your frontend to talk to this backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def cleanup_file(path: str):
    """Background task to remove temporary file after request completes."""
    if os.path.exists(path):
        os.remove(path)

@app.post("/analyze")
async def analyze_code(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Endpoint to upload a Python file and get static analysis metadata.
    """
    # 1. Validate file type
    if not file.filename.endswith('.py'):
        raise HTTPException(status_code=400, detail="Only .py files are allowed")

    # 2. Save uploaded file to a temporary directory
    # We need to save it because your analyzer.py uses Path.read_text()
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, file.filename)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 3. Run your existing Analyzer
        analyzer = PythonStaticAnalyzer()
        # Your analyzer returns a Dict with 'imports', 'functions', 'risk_scores'
        result = analyzer.analyze_file(temp_path)
        
        # 4. Schedule cleanup (delete file after response is sent)
        background_tasks.add_task(cleanup_file, temp_path)
        
        return result

    except Exception as e:
        # Ensure cleanup happens even if analysis fails
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

