// Voice Input Module - Web Speech API Integration for Vietnamese

// State Management
let recognition = null;
let isListening = false;
let voiceBtn = null;
let voiceIcon = null;
let voiceTaskInput = null;
let retryCount = 0;
const MAX_RETRIES = 3;
let ignoreEndEvent = false;

// Configuration
const VOICE_CONFIG = {
  lang: "vi-VN", // Vietnamese language
  continuous: true, // Keep listening until stopped
  interimResults: false, // Show partial results
  maxAlternatives: 1, // Only use best match
};

/**
 * Initialize Voice Input functionality
 * @returns {boolean} Whether initialization was successful
 */
function initVoiceInput() {
  voiceBtn = document.getElementById("voice-btn");
  voiceIcon = document.getElementById("voice-icon");
  voiceTaskInput = document.getElementById("user-task");

  if (!voiceBtn || !voiceTaskInput) {
    console.warn("Voice input elements not found");
    return false;
  }

  // 1. Detect Browser Compatibility
  const isEdge = /Edg/.test(navigator.userAgent);
  // @ts-ignore
  const hasAPI =
    "webkitSpeechRecognition" in window || "SpeechRecognition" in window;

  // Specific handler for unsupported/blocked scenarios
  const handleUnsupported = (message) => {
    voiceBtn.addEventListener("click", () => {
      showVoiceError(message);
    });
    // Ensure button is visible but interactive
    voiceBtn.style.display = "flex";
    return true;
  };

  // Case 1: Edge (Known issues)
  if (isEdge) {
    console.warn("Voice input disabled on Edge");
    return handleUnsupported(
      "Trình duyệt Edge chưa hỗ trợ đầy đủ. Vui lòng sử dụng <b>Google Chrome</b>.",
    );
  }

  // Case 2: API Missing (e.g. Firefox, or HTTP context on iOS)
  if (!hasAPI) {
    console.warn("Web Speech API not found");
    return handleUnsupported(
      "Trình duyệt của bạn không hỗ trợ nhận diện giọng nói. Vui lòng thử <b>Google Chrome</b>.",
    );
  }

  // 2. Initialize API (Supported Environment)
  const SpeechRecognition =
    // @ts-ignore
    window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();

  // Configure
  recognition.lang = VOICE_CONFIG.lang;
  recognition.continuous = VOICE_CONFIG.continuous;
  recognition.interimResults = VOICE_CONFIG.interimResults;
  recognition.maxAlternatives = VOICE_CONFIG.maxAlternatives;

  // Event handlers
  recognition.onstart = handleVoiceStart;
  recognition.onresult = handleVoiceResult;
  recognition.onerror = handleVoiceError;
  recognition.onend = handleVoiceEnd;

  // Button click handler
  voiceBtn.addEventListener("click", toggleVoiceInput);

  console.log("Voice input initialized with language:", VOICE_CONFIG.lang);
  return true;
}

/**
 * Toggle listening state
 */
function toggleVoiceInput() {
  if (isListening) {
    stopListening();
  } else {
    retryCount = 0; // Reset retry count on manual start
    startListening();
  }
}

/**
 * Start listening for voice input
 */
function startListening() {
  ignoreEndEvent = false;
  try {
    recognition.start();
  } catch (e) {
    console.error("Voice recognition start error:", e);
    // May already be running, try to stop and restart
    try {
      recognition.stop();
      setTimeout(() => {
        if (!isListening) recognition.start();
      }, 100);
    } catch (e2) {
      console.error("Voice recognition restart error:", e2);
    }
  }
}

/**
 * Stop listening
 */
function stopListening() {
  ignoreEndEvent = true; // Prevent retry on manual stop
  try {
    recognition.stop();
  } catch (e) {
    console.error("Voice recognition stop error:", e);
  }
}

// Track current input value to append with transcript
let currentInputValue = "";

/**
 * Handle voice recognition start event
 */
function handleVoiceStart() {
  isListening = true;
  currentInputValue = voiceTaskInput.value.trim();
  updateVoiceButtonState();
  console.log("Voice recognition started");
}

/**
 * Handle voice recognition result event
 * @param {any} event
 */
function handleVoiceResult(event) {
  let finalTranscript = "";
  for (let i = event.resultIndex; i < event.results.length; i++) {
    const result = event.results[i];
    finalTranscript += result[0].transcript;
  }

  // Append final transcript to textarea
  if (finalTranscript) {
    const newValue = currentInputValue
      ? currentInputValue + " " + finalTranscript
      : finalTranscript;
    voiceTaskInput.value = newValue;

    // Trigger input event for any listeners
    voiceTaskInput.dispatchEvent(new Event("input", { bubbles: true }));

    // Auto scroll bottom
    voiceTaskInput.scrollTop = voiceTaskInput.scrollHeight;
  }
}

/**
 * Handle voice recognition error event
 * @param {any} event
 */
function handleVoiceError(event) {
  console.error("Voice recognition error:", event.error);

  let errorMessage = "";
  let shouldRetry = false;

  switch (event.error) {
    case "not-allowed":
    case "permission-denied":
      errorMessage =
        "Vui lòng kiểm tra quyền truy cập microphone trong cài đặt trình duyệt.";
      ignoreEndEvent = true; // Don't retry if permission is denied
      break;
    case "no-speech":
      // No speech detected, just stop silently or retry if continuous
      return;
    case "network":
      shouldRetry = true;
      errorMessage = "Lỗi kết nối mạng.";
      break;
    case "aborted":
      // User aborted, no need to show error
      return;
    default:
      errorMessage = "Lỗi nhận diện giọng nói: " + event.error;
  }

  if (shouldRetry && retryCount < MAX_RETRIES) {
    console.log(`Retrying... (${retryCount + 1}/${MAX_RETRIES})`);
    retryCount++;
    ignoreEndEvent = true; // Prevent onend from processing default logic
    setTimeout(() => {
      try {
        recognition.stop(); // Ensure stopped before restarting
      } catch (e) {}
      setTimeout(startListening, 300);
    }, 100);
    return;
  }

  if (errorMessage && !ignoreEndEvent) {
    // Only show error if we're not ignoring it (e.g. manual stop or retry)
    showVoiceError(errorMessage);
  }
}

/**
 * Handle voice recognition end event
 */
function handleVoiceEnd() {
  // If we are retrying or manually stopped, don't update state to stopped yet
  if (ignoreEndEvent) {
    return;
  }

  // If user just stopped talking but didn't click stop (and continuous is true),
  // some browsers fire onend. We might want to restart here if we want truly "continuous".
  // But for now, let's treat it as a stop to be safe and save resources.

  isListening = false;
  updateVoiceButtonState();
  console.log("Voice recognition ended");
}

/**
 * Update voice button visual state
 */
function updateVoiceButtonState() {
  if (!voiceBtn) return;

  if (isListening) {
    voiceBtn.classList.add("voice-listening");
    voiceBtn.title = "Đang ghi âm... (nhấn để dừng)";
  } else {
    voiceBtn.classList.remove("voice-listening");
    voiceBtn.title = "Nhập bằng giọng nói (Tiếng Việt)";
  }

  // Re-render Lucide icons to update appearance
  if (typeof lucide !== "undefined") {
    lucide.createIcons();
  }
}

/**
 * Show voice error message using app's dialog system
 * @param {string} message
 */
function showVoiceError(message) {
  if (typeof showAlert === "function") {
    showAlert(message, { type: "warning" });
  } else {
    console.warn("Voice Error:", message);
    alert(message);
  }
}

// Initialize on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  initVoiceInput();
});
