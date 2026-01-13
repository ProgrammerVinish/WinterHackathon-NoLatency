// DOM Elements
const uploadBtn = document.getElementById("upload-btn");
const fileInput = document.getElementById("file-input");
const fileTree = document.getElementById("file-tree");
const codeContent = document.getElementById("code-content");
const fileNameDisplay = document.getElementById("file-name-display");
const analysisContent = document.getElementById("analysis-content");
const geminiPanel = document.getElementById("gemini-panel");
const geminiContent = document.getElementById("gemini-content");
const btnAsk = document.getElementById("btn-ask-gemini");
const API_BASE_URL = "https://winterhackathon-nolatency.onrender.com";

let currentFile = null;
let currentSelection = null;
let functionCache = {};

// --- Event Listeners ---
uploadBtn.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", () => {
  if (fileInput.files.length) handleFileUpload(fileInput.files[0]);
});
btnAsk.addEventListener("click", fetchExplanation);

// --- Core Logic ---

async function handleFileUpload(file) {
  currentFile = file;
  functionCache = {}; // Clear cache

  // UI Updates
  fileTree.innerHTML = `<div class="file-item active">📄 ${file.name}</div>`;
  fileNameDisplay.innerText = file.name;
  codeContent.innerText = "Loading code...";
  analysisContent.innerHTML = '<div class="empty-state">Analyzing...</div>';
  geminiPanel.classList.add("hidden");

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) throw new Error("Analysis failed");
    const data = await response.json();

    // 1. Render Source Code (New!)
    codeContent.textContent = data.source_code || "# No source code returned";
    Prism.highlightElement(codeContent); // Trigger Syntax Highlighting

    // 2. Render Analysis Side Panel
    renderAnalysis(data.functions);
  } catch (error) {
    console.error(error);
    codeContent.innerText = "Error loading file.";
    analysisContent.innerHTML = `<div class="empty-state" style="color:#ff8f8f">Error: ${error.message}</div>`;
  }
}

function renderAnalysis(functions) {
  analysisContent.innerHTML = "";

  if (!functions || functions.length === 0) {
    analysisContent.innerHTML =
      '<div class="empty-state">No functions found.</div>';
    return;
  }

  functions.forEach((func) => {
    const item = document.createElement("div");
    item.className = "func-item";

    item.innerHTML = `
            <div class="func-header">
                <span class="func-name">${func.name}</span>
                <span class="badge ${func.risk_score.risk_level}">${func.risk_score.risk_level}</span>
            </div>
            <div class="func-reason">${func.risk_score.risk_reason}</div>
        `;

    item.addEventListener("click", () => selectFunction(item, func));
    analysisContent.appendChild(item);
  });
}

function selectFunction(element, funcData) {
  // Visual Selection
  document
    .querySelectorAll(".func-item")
    .forEach((el) => el.classList.remove("selected"));
  element.classList.add("selected");

  currentSelection = funcData;

  // Show Gemini Panel
  geminiPanel.classList.remove("hidden");
  
  // Check Cache
  if (functionCache[funcData.name]) {
    geminiContent.innerHTML = marked.parse(functionCache[funcData.name]);
    btnAsk.innerText = "Explain Again";
  } else {
    geminiContent.innerHTML =
      "Click the button to generate an AI explanation for this function.";
    btnAsk.innerText = "Explain Function";
  }
}

async function fetchExplanation() {
  if (!currentFile || !currentSelection) return;
  btnAsk.disabled = true;


  btnAsk.innerText = "Thinking...";
  geminiContent.innerHTML =
    '<div class="empty-state">Gemini is analyzing...</div>';

  const formData = new FormData();
  formData.append("file", currentFile);

  try {
    const response = await fetch(`${API_BASE_URL}/explain?function_name=${currentSelection.name}`, {
        method: "POST",
        body: formData,
      }
    );

    const data = await response.json();
    functionCache[currentSelection.name] = data.explanation;

    // 1. Convert Markdown to HTML
    let htmlContent = marked.parse(data.explanation);

    // 2. Wrap H3 sections in "card" divs (The Magic Step)
    // This regex finds <h3>...</h3> and wraps it and following content in <div class="expl-card">
    htmlContent = htmlContent.replace(
      /<h3>/g,
      '</div><div class="expl-card"><h3>'
    );
    htmlContent = htmlContent.replace(/^<\/div>/, ""); // Remove the first empty closing div
    htmlContent += "</div>"; // Close the last div
    htmlContent = htmlContent.replace(
      /(HIGH|MEDIUM|LOW)/g,
      '<span class="risk-text $1">$1</span>'
    );
    geminiContent.innerHTML = htmlContent;
    btnAsk.innerText = "Explain Again";
  } catch (error) {
    console.error(error);
    geminiContent.innerHTML =
      '<div class="empty-state">Error fetching explanation.</div>';
    btnAsk.innerText = "Try Again";
  }
  btnAsk.disabled = false;
}