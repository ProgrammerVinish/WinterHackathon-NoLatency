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