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
    Endpoint to upload a Python file and get static analysis metadata AND source code.
    """
    if not file.filename.endswith('.py'):
        raise HTTPException(status_code=400, detail="Only .py files are allowed")

    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, file.filename)
    
    try:
        # 1. Save file to disk
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. Read the source code text (NEW STEP)
        with open(temp_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        # 3. Run Analysis
        analyzer = PythonStaticAnalyzer()
        result = analyzer.analyze_file(temp_path)
        
        # 4. Attach source code to the result (NEW STEP)
        result["source_code"] = source_code
        
        background_tasks.add_task(cleanup_file, temp_path)
        
        return result

    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/explain")
async def explain_function(
    function_name: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Endpoint to upload a file and get a Gemini explanation for a specific function.
    """
    # Check for API Key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Server API key not configured")

    # Save temp file
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, file.filename)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Run Analysis first
        analyzer = PythonStaticAnalyzer()
        analysis_result = analyzer.analyze_file(temp_path)
        
        # Find the specific function requested
        target_func = next(
            (f for f in analysis_result.get("functions", []) if f["name"] == function_name), 
            None
        )
        
        if not target_func:
            raise HTTPException(status_code=404, detail=f"Function '{function_name}' not found in file")

        # Prepare context
        file_context = {
            "imports": analysis_result.get("imports", []),
            "file_dependencies": analysis_result.get("file_dependencies", [])
        }

        # Run your existing Gemini Explainer
        explainer = GeminiExplainer(api_key=api_key)
        explanation = explainer.explain_function(target_func, file_context)
        
        background_tasks.add_task(cleanup_file, temp_path)
        
        return {
            "function": function_name,
            "explanation": explanation,
            "risk_score": target_func.get("risk_score")
        }

    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Run the server
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

#http://localhost:8000/docs