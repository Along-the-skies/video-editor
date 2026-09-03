const API = "";
let sessionId = null;
let isNavigatingAway = false;

async function createSession() {
  const response = await fetch(`${API}/session`, { method: "POST" });
  if (!response.ok) {
    throw new Error("Failed to create session");
  }
  const data = await response.json();
  sessionId = data.session_id;
  return sessionId;
}

async function uploadFile(endpoint, file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API}${endpoint}/${sessionId}`, {
    method: "POST",
    body: formData
  });
  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || "Upload Failed");
  }
  return response.json();
}

const generateButton = document.getElementById("generateButton");
if (generateButton) {
  generateButton.addEventListener("click", async function () {
    const audio = document.getElementById("audioInput").files[0];
    const first = document.getElementById("firstImage").files[0];
    const last = document.getElementById("lastImage").files[0];
    const middle = document.getElementById("middleFiles").files;
    const status = document.getElementById("status");
    if (!audio || !first || !last) {
      status.textContent = "Please select the narration,first image and last image";
      return;
    }
    try {
      generateButton.disabled = true;
      status.textContent = "Creating session...";
      await createSession();
      status.textContent = "Uploading narration...";
      await uploadFile("/upload/audio", audio);
      status.textContent = "Uploading First image...";
      await uploadFile("/upload/first", first);
      for (let i = 0; i < middle.length; i++) {
        status.textContent = `Uploading media ${i + 1} of ${middle.length}...`;
        await uploadFile("/upload/media", middle[i]);
      }
      status.textContent = "Uploading Last image...";
      await uploadFile("/upload/last", last);
      status.textContent = "Uploads complete!";
      isNavigatingAway = true;
      window.location.href = `generate.html?session_id=${encodeURIComponent(sessionId)}`;
    } catch (error) {
      console.error(error);
      status.textContent = `Error: ${error.message}`;
      generateButton.disabled = false;
    }
  });
}

const generateBtn = document.getElementById("generate-btn");
if (generateBtn) {
  const readyState = document.querySelector(".state--ready");
  const workingState = document.querySelector(".state--working");
  const doneState = document.querySelector(".state--done");
  const errorState = document.querySelector(".state--error");
  const videoPlayer = document.querySelector(".previw-player");
  const downloadLink = document.getElementById("download-link");
  const retryBtn = document.getElementById("retry-btn");
  const errorMessage = document.querySelector(".error-message");
  const currentSessionId = new URLSearchParams(window.location.search).get("session_id");

  if (currentSessionId) {
    sessionId = currentSessionId;
  }

  async function generateVideo() {
    if (!currentSessionId) {
      showError("No session ID found.");
      return;
    }
    readyState.hidden = true;
    workingState.hidden = false;
    doneState.hidden = true;
    errorState.hidden = true;
    try {
      const response = await fetch(`${API}/generate/${encodeURIComponent(currentSessionId)}`, {
        method: "POST"
      });
      if (!response.ok) {
        const error = await response.json().catch(() => null);
        throw new Error(error?.detail || "Failed to generate video");
      }
      workingState.hidden = true;
      doneState.hidden = false;
      const downloadUrl = `${API}/download/${encodeURIComponent(currentSessionId)}`;
      videoPlayer.src = downloadUrl;
      downloadLink.href = downloadUrl;
      downloadLink.download = "video.mp4";
    } catch (error) {
      console.error(error);
      showError(error.message);
    }
  }

  function showError(message) {
    readyState.hidden = true;
    workingState.hidden = true;
    doneState.hidden = true;
    errorState.hidden = false;
    errorMessage.textContent = message;
  }

  generateBtn.addEventListener("click", generateVideo);
  if (retryBtn) {
    retryBtn.addEventListener("click", generateVideo);
  }
}

function showSelectedFile(inputId, outputId) {
  const input = document.getElementById(inputId);
  const output = document.getElementById(outputId);
  if (!input || !output) return;
  input.addEventListener("change", () => {
    if (!input.files.length) {
      output.textContent = "";
      return;
    }
    if (input.files.length === 1) {
      output.textContent = input.files[0].name;
    } else {
      output.textContent = `${input.files.length} files selected`;
    }
  });
}

showSelectedFile("audioInput", "audioName");
showSelectedFile("firstImage", "firstImageName");
showSelectedFile("lastImage", "lastImageName");
showSelectedFile("middleFiles", "middleFilesName");

window.addEventListener("beforeunload", (event) => {
  if (sessionId && !isNavigatingAway) {
    event.preventDefault();
    event.returnValue = "";
  }
});

window.addEventListener("pagehide", () => {
  if (sessionId && !isNavigatingAway) {
    fetch(`${API}/session/${sessionId}`, {
      method: "DELETE",
      keepalive: true
    }).catch(() => {});
  }
});
