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
