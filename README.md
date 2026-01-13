# ExplainIt

## Description

ExplainIt is a read-only AI-assisted tool that helps developers understand unfamiliar or legacy code before making changes.

When working with existing codebases, developers often lack clarity about why certain code exists, where it is used, and what might break if it is modified. This uncertainty leads to bugs, regressions, and wasted time.

ExplainIt addresses this problem by performing static analysis to extract structural information from the code and using AI to generate clear explanations and risk insights — without modifying or uploading the source code.

---

## Demo Video Link

🎥 Demo Video: https://drive.google.com/drive/folders/1WrDemf2-dkfehcgT4O1fr_CgDzUCc_S0

---

## Features

- Read-only static analysis of Python source code using AST parsing
- Detection of functions, imports, parameters, and dependencies
- Rule-based risk classification (Low / Medium / High) based on API calls, usage patterns, and function types
- AI-generated explanations for code intent and impact using Google Gemini API
- Interactive web-based dashboard with code viewer and analysis panel
- Privacy-first design (raw source code is never sent to AI - only structured metadata)

---

## Tech Stack

- Backend: Python, FastAPI
- Static Analysis: Python AST (Abstract Syntax Tree)
- AI: Google Gemini API (gemini-2.5-flash-lite)
- Frontend: Vanilla JavaScript, HTML5, CSS3, Prism.js (syntax highlighting), marked.js (markdown parsing)

---

## Google Technologies Used

- **Gemini API** – Used to generate natural-language explanations from structured metadata. The API receives only function metadata (name, parameters, calls, risk scores) and never the raw source code.

---

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- A Google Gemini API key (get one from [Google AI Studio](https://makersuite.google.com/app/apikey))
- A modern web browser

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the backend directory:
   ```bash
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

4. Start the FastAPI server:
   ```bash
   python server.py
   ```

   The server will run on `http://localhost:8000`. You can also access the API documentation at `http://localhost:8000/docs`.

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Open `index.html` in a web browser, or use a local web server:
   ```bash
   # Using Python's built-in server
   python -m http.server 8080
   ```

3. Access the application at `http://localhost:8080` (or the port you specified).

### Usage

1. Start the backend server (see Backend Setup above).
2. Open the frontend in your browser.
3. Click "Upload File" and select a Python (.py) file.
4. The application will analyze the code and display:
   - Source code with syntax highlighting
   - Function list with risk scores
   - Click on any function to get AI-generated explanations

---

## Team Members

- Vinish
- Veol Steve Jose
- Vaishali Kolpe
- Sanjothomas V S
