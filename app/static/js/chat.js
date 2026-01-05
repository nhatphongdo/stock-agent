// Chat Module - Conversation Management

// Chat Variables (Initialized in DOMContentLoaded)
let submitBtn,
  generalBtn,
  sectorBtn,
  userTaskInput,
  messagesContainer,
  chatContainer;

/**
 * Initialize chat DOM elements.
 */
function initChatElements() {
  submitBtn = document.getElementById("submit-btn");
  generalBtn = document.getElementById("general-btn");
  sectorBtn = document.getElementById("sector-btn");
  userTaskInput = document.getElementById("user-task");
  messagesContainer = document.getElementById("messages");
  chatContainer = document.getElementById("chat-container");
}

// --- Conversation Persistence (sessionStorage) ---
/**
 * Saves the current conversation to sessionStorage.
 */
function saveConversation() {
  if (!messagesContainer) initChatElements();
  sessionStorage.setItem(
    CONFIG.STORAGE_KEYS.CONVERSATION,
    messagesContainer.innerHTML,
  );
}

/**
 * Loads the conversation from sessionStorage.
 */
function loadConversation() {
  if (!messagesContainer || !chatContainer) initChatElements();
  const saved = sessionStorage.getItem(CONFIG.STORAGE_KEYS.CONVERSATION);
  if (saved) {
    messagesContainer.innerHTML = saved;
    lucide.createIcons({ root: messagesContainer });
    chatContainer.scrollTop = chatContainer.scrollHeight;
    // Extract symbols from loaded conversation
    extractAndUpdateSymbols();
  }
}

/**
 * Extract stock symbols from the entire conversation and update chart symbol selector.
 * Uses the same stock-ticker class that processContent() adds to valid symbols.
 */
function extractAndUpdateSymbols() {
  if (!messagesContainer) return;
  const tickers = messagesContainer.querySelectorAll(".stock-ticker");
  if (tickers.length > 0) {
    const symbols = [
      ...new Set(
        [...tickers].map(
          (el) => /** @type {HTMLElement} */ (el).dataset.symbol,
        ),
      ),
    ];
    if (typeof updateChartSymbolSelector === "function") {
      updateChartSymbolSelector(symbols);
    }
  }
}

/**
 * Clears the conversation and resets to welcome message.
 */
function clearConversation() {
  if (!messagesContainer) initChatElements();
  // Build greeting with user name if available
  const userName =
    currentUser && currentUser.full_name ? currentUser.full_name : "";
  const greeting = userName
    ? `Xin chào <b>${userName}</b>! Tôi là <b>Stock Trading Assistant</b>. Hãy nhập yêu cầu phân tích để tôi có thể hỗ trợ bạn tìm kiếm cơ hội đầu tư tốt nhất.`
    : `Xin chào! Tôi là <b>Stock Trading Assistant</b>. Hãy nhập yêu cầu phân tích để tôi có thể hỗ trợ bạn tìm kiếm cơ hội đầu tư tốt nhất.`;

  messagesContainer.innerHTML = "";
  const template = /** @type {HTMLTemplateElement} */ (
    document.getElementById("welcome-message-template")
  );
  if (template) {
    const clone = document.importNode(template.content, true);
    const welcomeText = /** @type {HTMLElement} */ (
      clone.querySelector(".welcome-text")
    );
    if (welcomeText) welcomeText.innerHTML = greeting;
    messagesContainer.appendChild(clone);
  } else {
    console.error("Template 'welcome-message-template' not found");
  }
  lucide.createIcons({ root: messagesContainer });
  sessionStorage.removeItem(CONFIG.STORAGE_KEYS.CONVERSATION);
}

/**
 * Creates initial bot message bubble with skeleton loading.
 * @param {string} id - The unique ID for the message.
 * @returns {HTMLElement} The message div element.
 */
function addInitialBotMessage(id) {
  if (!messagesContainer) initChatElements();
  const messageDiv = document.createElement("div");
  messageDiv.className = "flex gap-4 group";
  messageDiv.id = id;

  const template = /** @type {HTMLTemplateElement} */ (
    document.getElementById("loading-message-template")
  );
  if (template) {
    messageDiv.appendChild(document.importNode(template.content, true));
  } else {
    console.error("Template 'loading-message-template' not found");
  }

  messagesContainer.appendChild(messageDiv);
  lucide.createIcons({ root: messageDiv });
  return messageDiv;
}

/**
 * Adds a message to the chat.
 * @param {string} sender - Either "bot" or "user".
 * @param {string} content - The message content.
 */
function addMessage(sender, content) {
  if (!messagesContainer || !chatContainer) initChatElements();

  if (sender === "bot") {
    const id = "bot-msg-" + Date.now();
    const div = addInitialBotMessage(id);
    div.querySelector(".markdown-content").innerHTML = processContent(content);
    return;
  }

  const messageDiv = document.createElement("div");
  messageDiv.className = "flex gap-4 justify-end group user-bubble-container";

  const template = /** @type {HTMLTemplateElement} */ (
    document.getElementById("user-message-template")
  );
  if (template) {
    const clone = document.importNode(template.content, true);
    const contentDiv = clone.querySelector(".user-markdown");
    if (contentDiv) contentDiv.innerHTML = marked.parse(content);
    messageDiv.appendChild(clone);
  } else {
    console.error("Template 'user-message-template' not found");
  }

  messagesContainer.appendChild(messageDiv);
  lucide.createIcons({ root: messageDiv });
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

/**
 * Analyzes a task by sending it to the backend.
 * @param {boolean} isGeneral - Whether this is a general market analysis.
 * @param {string} [sectorCode] - Optional ICB sector code for sector analysis.
 * @param {string} [sectorName] - Optional sector name for display.
 * @returns {Promise<void>}
 */
async function analyzeTask(
  isGeneral = false,
  sectorCode = null,
  sectorName = null,
) {
  if (
    !submitBtn ||
    !generalBtn ||
    !sectorBtn ||
    !userTaskInput ||
    !chatContainer
  )
    initChatElements();

  let task = null;

  // Determine analysis type and set task/message
  if (sectorCode && sectorName) {
    // Sector analysis
    addMessage("user", `✨ Phân tích tổng quan ngành ${sectorName}`);
  } else if (!isGeneral) {
    // User-provided task
    task = userTaskInput.value.trim();
    if (!task) return;
    addMessage("user", task);
    userTaskInput.value = "";
  } else {
    // General market analysis
    addMessage("user", "✨ Phân tích tổng quan thị trường");
  }

  submitBtn.disabled = true;
  generalBtn.disabled = true;
  sectorBtn.disabled = true;
  chatContainer.scrollTop = chatContainer.scrollHeight;

  // Prepare bot message bubble for streaming
  const botMessageId = "bot-msg-" + Date.now();
  const messageDiv = addInitialBotMessage(botMessageId);
  const contentDiv = messageDiv.querySelector(".markdown-content");
  let fullContent = "";
  chatContainer.scrollTop = chatContainer.scrollHeight;

  try {
    // Fetch user's current stocks from portfolio to pass to agent
    let userStocks = [];
    if (currentUser) {
      try {
        const stocksRes = await fetch(`/users/${currentUser.id}/stocks`);
        if (stocksRes.ok) {
          const stocksData = await stocksRes.json();
          userStocks = stocksData.map(
            (s) => `${s.stock_name} (${s.avg_price})`,
          );
        }
      } catch (e) {
        console.warn("Could not fetch portfolio for analysis:", e);
      }
    }

    const response = await fetch("/stock-analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        task: task,
        stocks: userStocks,
        blacklist: currentUser ? currentUser.black_list : null,
        whitelist: currentUser ? currentUser.white_list : null,
        return_rate: currentUser ? currentUser.return_rate : null,
        dividend_rate: currentUser ? currentUser.dividend_rate : null,
        profit_rate: currentUser ? currentUser.profit_rate : null,
        sector: sectorCode,
        sector_name: sectorName,
      }),
    });

    if (!response.ok) throw new Error("Network response was not ok");

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    // Track reasoning and final content separately
    let reasoningContent = "";
    let finalContent = "";
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Process complete JSON lines
      const lines = buffer.split("\n");
      buffer = lines.pop() || ""; // Keep incomplete line in buffer

      for (const line of lines) {
        if (!line.trim()) continue;

        try {
          const parsed = JSON.parse(line);

          if (parsed.type === "reasoning") {
            reasoningContent += parsed.chunk || "";
          } else if (parsed.type === "final") {
            finalContent += parsed.chunk || "";
          } else if (parsed.type === "error") {
            finalContent += `\n\n❌ Error: ${parsed.message}`;
          }

          // Update UI with both sections
          let displayHtml = "";

          // Determine if still processing (no final content yet)
          const isStillProcessing = !finalContent.trim();

          // Reasoning section (collapsible, default collapsed)
          if (reasoningContent.trim()) {
            const reasoningTemplate = /** @type {HTMLTemplateElement} */ (
              document.getElementById("reasoning-template")
            );
            if (reasoningTemplate) {
              const clone = document.importNode(
                reasoningTemplate.content,
                true,
              );
              const details = clone.querySelector("details");
              const iconContainer = clone.querySelector(".icon-container");
              const statusContainer = clone.querySelector(".status-container");
              const contentBody = clone.querySelector(
                ".reasoning-content-body",
              );

              if (isStillProcessing) details.open = true;

              if (isStillProcessing) {
                iconContainer.innerHTML =
                  '<span class="inline-block w-4 h-4 border-2 border-primary-500 border-t-transparent rounded-full animate-spin"></span>';
                statusContainer.innerHTML =
                  '<span class="text-xs text-primary-500 animate-pulse">đang xử lý...</span>';
              } else {
                iconContainer.innerHTML =
                  '<i data-lucide="brain" class="w-4 h-4"></i>';
                statusContainer.innerHTML =
                  '<span class="text-xs opacity-60">(click để mở rộng)</span>';
              }

              contentBody.innerHTML = processContent(reasoningContent);

              // Get HTML string
              const temp = document.createElement("div");
              temp.appendChild(clone);
              displayHtml += temp.innerHTML;
            }
          }

          // Final section (always visible)
          if (finalContent.trim()) {
            displayHtml += processContent(finalContent);
          }

          contentDiv.innerHTML = displayHtml;
          lucide.createIcons({ root: contentDiv });
          chatContainer.scrollTop = chatContainer.scrollHeight;
        } catch (e) {
          // Fallback for non-JSON responses (backward compatibility)
          fullContent += line;
          contentDiv.innerHTML = processContent(fullContent);
          chatContainer.scrollTop = chatContainer.scrollHeight;
        }
      }
    }
  } catch (error) {
    console.error("Error:", error);
    if (contentDiv) {
      contentDiv.innerHTML =
        "❌ Đã xảy ra lỗi khi kết nối với máy chủ: " + error.message;
    }
  } finally {
    submitBtn.disabled = false;
    generalBtn.disabled = false;
    sectorBtn.disabled = false;
    chatContainer.scrollTop = chatContainer.scrollHeight;
    // Save conversation to sessionStorage
    saveConversation();

    // Extract symbols from the entire conversation and update chart symbol selector
    extractAndUpdateSymbols();
  }
}

// Initialize Chat Event Listeners
document.addEventListener("DOMContentLoaded", () => {
  initChatElements();

  // Load conversation from sessionStorage
  loadConversation();

  // Add event listeners
  if (submitBtn) {
    submitBtn.addEventListener("click", () => analyzeTask(false));
  }
  if (generalBtn) {
    generalBtn.addEventListener("click", () => analyzeTask(true));
  }
  if (userTaskInput) {
    userTaskInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        analyzeTask(false);
      }
    });
  }

  // --- Table Drag-to-Scroll ---
  let isDraggingTable = false;
  let startXTable;
  let scrollLeftTable;
  let activeTableWrapper = null;

  if (messagesContainer) {
    messagesContainer.addEventListener("mousedown", (e) => {
      const wrapper = e.target.closest(".table-wrapper");
      if (!wrapper) return;

      isDraggingTable = true;
      wrapper.classList.add("is-dragging");
      activeTableWrapper = wrapper;
      startXTable = e.pageX - wrapper.offsetLeft;
      scrollLeftTable = wrapper.scrollLeft;
    });
  }

  window.addEventListener("mouseup", () => {
    if (!activeTableWrapper) return;
    isDraggingTable = false;
    activeTableWrapper.classList.remove("is-dragging");
    activeTableWrapper = null;
  });

  window.addEventListener("mousemove", (e) => {
    if (!isDraggingTable || !activeTableWrapper) return;
    e.preventDefault();
    const x = e.pageX - activeTableWrapper.offsetLeft;
    const walk = (x - startXTable) * 2; // Scroll speed factor
    activeTableWrapper.scrollLeft = scrollLeftTable - walk;
  });

  // --- Stock Ticker Click Handler ---
  if (chatContainer) {
    chatContainer.addEventListener("click", (e) => {
      const ticker = e.target.closest(".stock-ticker");
      if (ticker) {
        const symbol = ticker.dataset.symbol;
        if (typeof selectStock === "function") {
          selectStock(symbol);
        } else {
          console.warn("selectStock function not found");
        }
      }
    });
  }
});
