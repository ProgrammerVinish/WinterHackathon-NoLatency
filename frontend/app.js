// DOM Elements
const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const resultsArea = document.getElementById("results-area");
const functionsList = document.getElementById("functions-list");
const fileNameTitle = document.getElementById("file-name-title");

let currentFile = null; // Store file for explanation requests

// --- Drag & Drop Handlers ---
dropZone.addEventListener("click", () => fileInput.click());

dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("dragover");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("dragover");
});

dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("dragover");
  if (e.dataTransfer.files.length) {
    handleFileUpload(e.dataTransfer.files[0]);
  }
});

fileInput.addEventListener("change", () => {
  if (fileInput.files.length) {
    handleFileUpload(fileInput.files[0]);
  }
});

// --- Upload & Analyze Logic ---
async function handleFileUpload(file) {
  currentFile = file; // Save for later
  fileNameTitle.innerText = `Analyzing: ${file.name}...`;
  resultsArea.style.display = "block";
  functionsList.innerHTML =
    '<p style="text-align:center; color:#666;">Analyzing code structure...</p>';

  const formData = new FormData();
  formData.append("file", file);

  try {
    // Call your Backend
    const response = await fetch("http://localhost:8000/analyze", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) throw new Error("Analysis failed");
    const data = await response.json();

    renderResults(data);
    fileNameTitle.innerText = `Analysis: ${file.name}`;
  } catch (error) {
    console.error(error);
    functionsList.innerHTML = `<p style="color:red; text-align:center;">Error: ${error.message}</p>`;
  }
}

// --- Render UI ---
function renderResults(data) {
  functionsList.innerHTML = "";

  if (data.functions.length === 0) {
    functionsList.innerHTML = "<p>No functions found in this file.</p>";
    return;
  }

  data.functions.forEach((func) => {
    const riskLevel = func.risk_score.risk_level;

    const div = document.createElement("div");
    div.className = "function-item";
    // Note: onclick now calls window.getExplanation because modules have different scopes
    div.innerHTML = `
            <div class="func-header">
                <div>
                    <span class="func-name">${func.name}()</span>
                    <br><small style="color:#666">Line: ${func.line_number} | Params: ${func.parameter_count}</small>
                </div>
                <div style="text-align:right">
                    <span class="risk-badge risk-${riskLevel}">${riskLevel} Risk</span>
                </div>
            </div>
            <p style="margin: 5px 0 15px 0; color: #4b5563;">
                <em>Reason: ${func.risk_score.risk_reason}</em>
            </p>
            <button class="btn-explain" onclick="getExplanation('${func.name}', this)">
                Ask Gemini to Explain
            </button>
            <div class="explanation-box" id="explain-${func.name}"></div>
        `;
    functionsList.appendChild(div);
  });
}

// --- Explain Logic ---
// We attach this to window so the HTML onclick="" can find it easily
window.getExplanation = async function (funcName, btnElement) {
  const outputBox = document.getElementById(`explain-${funcName}`);

  // UI Loading State
  btnElement.disabled = true;
  btnElement.innerHTML = `<span class="loading"></span> Explaining...`;

  const formData = new FormData();
  formData.append("file", currentFile); // Resend the file for context

  try {
    // Call your Backend Explain Endpoint
    const response = await fetch(
      `http://localhost:8000/explain?function_name=${funcName}`,
      {
        method: "POST",
        body: formData,
      }
    );

    const data = await response.json();

    // Show Explanation
    outputBox.style.display = "block";
    // Simple formatting for newlines
    outputBox.innerHTML = `<strong>Gemini says:</strong><br><br>${data.explanation.replace(
      /\n/g,
      "<br>"
    )}`;

    // Reset Button
    btnElement.innerHTML = "Explain Again";
    btnElement.disabled = false;
  } catch (error) {
    btnElement.innerHTML = "Error - Try Again";
    btnElement.disabled = false;
    alert("Failed to get explanation: " + error.message);
  }
};
