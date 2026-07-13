const fileInput = document.querySelector("#audio-file");
const dropZone = document.querySelector("#drop-zone");
const fileCard = document.querySelector("#file-card");
const fileName = document.querySelector("#file-name");
const fileSize = document.querySelector("#file-size");
const clearButton = document.querySelector("#clear-file");
const preview = document.querySelector("#audio-preview");
const analyzeButton = document.querySelector("#analyze");
const buttonLabel = document.querySelector("#button-label");
const statusLine = document.querySelector("#status");
const emptyResult = document.querySelector("#empty-result");
const results = document.querySelector("#results");
const winnerName = document.querySelector("#winner-name");
const audioMeta = document.querySelector("#audio-meta");
const scoreList = document.querySelector("#scores");
const featureList = document.querySelector("#features");
const modelId = document.querySelector("#model-id");
const limitLabel = document.querySelector("#limit-label");

let selectedFile = null;
let previewUrl = null;
let maxUploadBytes = 2 * 1024 * 1024;

const classNames = {
  steady_tone: "Steady tone",
  pulsed_tone: "Pulsed tone",
  broadband_texture: "Broadband texture",
};

function humanBytes(value) {
  if (value < 1024) return `${value} B`;
  return `${(value / (1024 * 1024)).toFixed(2)} MiB`;
}

function resetResults() {
  emptyResult.classList.remove("hidden");
  results.classList.add("hidden");
  modelId.textContent = "Awaiting input";
}

function clearSelection() {
  selectedFile = null;
  fileInput.value = "";
  fileCard.classList.add("hidden");
  preview.classList.add("hidden");
  preview.removeAttribute("src");
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = null;
  analyzeButton.disabled = true;
  statusLine.textContent = "";
  resetResults();
}

function chooseFile(file) {
  statusLine.textContent = "";
  resetResults();
  if (!file || !file.name.toLowerCase().endsWith(".wav")) {
    clearSelection();
    statusLine.textContent = "Choose an uncompressed PCM WAV file.";
    return;
  }
  if (file.size > maxUploadBytes) {
    clearSelection();
    statusLine.textContent = `That file is larger than ${humanBytes(maxUploadBytes)}.`;
    return;
  }
  selectedFile = file;
  fileName.textContent = file.name;
  fileSize.textContent = humanBytes(file.size);
  fileCard.classList.remove("hidden");
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = URL.createObjectURL(file);
  preview.src = previewUrl;
  preview.classList.remove("hidden");
  analyzeButton.disabled = false;
}

function renderResult(payload) {
  winnerName.textContent = payload.classification.display_name;
  const duration = Number(payload.audio.duration_seconds).toFixed(2);
  audioMeta.textContent = `${duration}s · ${payload.audio.sample_rate_hz.toLocaleString()} Hz · ${payload.audio.channels === 1 ? "mono" : "stereo"}`;
  modelId.textContent = payload.model.id;
  scoreList.replaceChildren();
  Object.entries(payload.relative_scores)
    .sort((left, right) => right[1] - left[1])
    .forEach(([classId, score]) => {
      const item = document.createElement("div");
      item.className = "score-row";
      const label = document.createElement("div");
      label.className = "score-label";
      const name = document.createElement("span");
      name.textContent = classNames[classId] || classId;
      const value = document.createElement("span");
      value.textContent = `${(score * 100).toFixed(1)}%`;
      label.append(name, value);
      const track = document.createElement("div");
      track.className = "score-track";
      const fill = document.createElement("span");
      fill.style.width = `${Math.max(0, Math.min(100, score * 100))}%`;
      track.append(fill);
      item.append(label, track);
      scoreList.append(item);
    });

  featureList.replaceChildren();
  Object.entries(payload.features).forEach(([name, value]) => {
    const wrapper = document.createElement("div");
    const term = document.createElement("dt");
    term.textContent = name.replaceAll("_", " ");
    const definition = document.createElement("dd");
    definition.textContent = Number(value).toFixed(5);
    wrapper.append(term, definition);
    featureList.append(wrapper);
  });
  emptyResult.classList.add("hidden");
  results.classList.remove("hidden");
}

async function classify() {
  if (!selectedFile) return;
  analyzeButton.disabled = true;
  analyzeButton.classList.add("loading");
  buttonLabel.textContent = "Comparing…";
  statusLine.textContent = "Reading acoustic features locally on the service…";
  try {
    const response = await fetch("/api/classify", {
      method: "POST",
      headers: { "Content-Type": "audio/wav", "X-Filename": selectedFile.name },
      body: selectedFile,
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error?.message || "The sound could not be processed.");
    renderResult(payload);
    statusLine.textContent = "Comparison complete. The temporary upload has been removed.";
  } catch (error) {
    resetResults();
    statusLine.textContent = error instanceof Error ? error.message : "The sound could not be processed.";
  } finally {
    analyzeButton.disabled = !selectedFile;
    analyzeButton.classList.remove("loading");
    buttonLabel.textContent = "Compare sound shape";
  }
}

fileInput.addEventListener("change", () => chooseFile(fileInput.files[0]));
clearButton.addEventListener("click", clearSelection);
analyzeButton.addEventListener("click", classify);
["dragenter", "dragover"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.add("dragging");
  });
});
["dragleave", "drop"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.remove("dragging");
  });
});
dropZone.addEventListener("drop", (event) => chooseFile(event.dataTransfer.files[0]));

fetch("/api/config")
  .then((response) => response.json())
  .then((config) => {
    maxUploadBytes = config.max_upload_bytes;
    limitLabel.textContent = `PCM WAV · up to ${humanBytes(maxUploadBytes)}`;
  })
  .catch(() => {});
