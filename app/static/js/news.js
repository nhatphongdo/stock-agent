/**
 * News Module - Handles news analysis and display
 */

// --- State ---
let lastFetchedNewsSymbol = null;

/**
 * Reset news state when stock changes
 */
function resetNewsState() {
  lastFetchedNewsSymbol = null;
}

/**
 * Check if news needs to be fetched for the current stock
 * @param {string} symbol - Stock symbol
 * @returns {boolean}
 */
function shouldFetchNews(symbol) {
  return symbol && symbol !== lastFetchedNewsSymbol;
}

/**
 * Trigger news fetch when switching to news tab or selecting a new stock
 * @param {string} symbol - Stock symbol
 * @param {string} companyName - Company name
 */
function triggerNewsAnalysis(symbol, companyName) {
  if (shouldFetchNews(symbol)) {
    fetchNewsAnalysis(symbol, companyName);
    lastFetchedNewsSymbol = symbol;
  }
}

/**
 * Fetch and display news analysis for a stock
 * @param {string} symbol - Stock symbol
 * @param {string} companyName - Company name
 */
async function fetchNewsAnalysis(symbol, companyName) {
  document.getElementById("news-tab-content-empty").classList.add("hidden");
  document
    .getElementById("news-tab-content-container")
    .classList.remove("hidden");

  const analysisContentEl = document.getElementById("news-analysis-content");
  const newsListContainer = document.getElementById("news-list-container");
  const newsCountBadge = document.getElementById("news-count-badge");

  let accumulatedText = "";

  try {
    const response = await fetch("/news-analysis", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbol: symbol, company_name: companyName }),
    });

    if (!response.ok)
      throw new Error("API Connection Error: " + response.status);

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    let isFirstChunk = true;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const evt = JSON.parse(line);
          if (evt.type === "content") {
            if (isFirstChunk) {
              if (analysisContentEl) analysisContentEl.innerHTML = "";
              isFirstChunk = false;
            }

            // Update Text
            accumulatedText += evt.chunk;
            if (analysisContentEl) {
              analysisContentEl.innerHTML =
                processContentNoTickers(accumulatedText);
            }
          } else if (evt.type === "data") {
            // Render News List
            renderNewsList(evt.news || [], newsListContainer, newsCountBadge);
          } else if (evt.type === "sentiment") {
            renderSentimentBadge(evt);
          } else if (evt.type === "error") {
            console.error("Stream Error:", evt.message);
            if (analysisContentEl)
              analysisContentEl.innerHTML += `<div class="text-red-500 text-xs mt-2">⚠️ ${evt.message}</div>`;
            isFirstChunk = false;
          }
        } catch (parseErr) {
          console.error("JSON Parse Error:", parseErr);
        }
      }
    }

    // End of stream check
    if (isFirstChunk && !accumulatedText) {
      if (analysisContentEl)
        analysisContentEl.innerHTML = `<div class="text-slate-500 italic text-sm">Không có dữ liệu phân tích.</div>`;
    }
  } catch (error) {
    console.error(error);
    if (analysisContentEl)
      analysisContentEl.innerHTML = `<div class="text-red-500 p-4">Lỗi: ${error.message}</div>`;
    if (newsListContainer) newsListContainer.innerHTML = "";
  }
}

/**
 * Render news list items
 * @param {Array} newsList - List of news items
 * @param {HTMLElement} container - Container element
 * @param {HTMLElement} countBadge - Badge to show count
 */
function renderNewsList(newsList, container, countBadge) {
  if (countBadge) {
    countBadge.textContent = String(newsList.length);
    countBadge.classList.remove("hidden");
  }

  if (container) {
    if (newsList.length === 0) {
      container.innerHTML = `<div class="text-sm text-slate-500 italic p-4">Không tìm thấy nguồn tin chi tiết.</div>`;
    } else {
      const template = /** @type {HTMLTemplateElement} */ (
        document.getElementById("news-item-template")
      );
      container.innerHTML = "";

      newsList.forEach((n) => {
        const isEvent =
          n.type && n.type !== "Tin tức" && n.type !== "Báo cáo phân tích";
        const isAnalysis = n.type === "Báo cáo phân tích";
        const icon = isEvent
          ? "calendar"
          : isAnalysis
            ? "file-text"
            : "newspaper";
        const iconColor = isEvent
          ? "text-amber-500"
          : isAnalysis
            ? "text-indigo-500"
            : "text-primary-500";
        const typeBadgeClass = isEvent
          ? "bg-amber-100 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400"
          : isAnalysis
            ? "bg-indigo-100 text-indigo-700 dark:bg-indigo-500/10 dark:text-indigo-400"
            : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300";

        const clone = /** @type {DocumentFragment} */ (
          template.content.cloneNode(true)
        );

        // Set link
        const link = /** @type {HTMLAnchorElement} */ (
          clone.querySelector("a")
        );
        link.href = n.link;

        // Set icon
        const iconContainer = clone.querySelector(".news-icon-container");
        iconContainer?.classList.add(iconColor);
        const iconEl = iconContainer?.querySelector("i");
        if (iconEl) iconEl.setAttribute("data-lucide", icon);

        // Set title
        const titleEl = clone.querySelector(".news-title");
        if (titleEl) titleEl.textContent = n.title;

        // Set description
        if (n.description) {
          const descEl = clone.querySelector(".news-description");
          if (descEl) {
            descEl.textContent = n.description;
            descEl.classList.remove("hidden");
          }
        }

        // Set type badge
        const typeBadge = clone.querySelector(".news-type-badge");
        if (typeBadge) {
          typeBadge.textContent = n.type || "Tin tức";
          typeBadge.className = `px-2 py-0.5 rounded font-bold uppercase tracking-wider ${typeBadgeClass}`;
        }

        // Set date
        const dateEl = clone.querySelector(".news-date");
        if (dateEl) dateEl.textContent = n.date;

        // Set source
        if (n.source) {
          const sourceSep = clone.querySelector(".news-source-separator");
          const sourceEl = clone.querySelector(".news-source");
          if (sourceSep) sourceSep.classList.remove("hidden");
          if (sourceEl) {
            sourceEl.textContent = n.source;
            sourceEl.classList.remove("hidden");
          }
        }

        container.appendChild(clone);
      });

      lucide.createIcons({ root: container });
    }
  }
}

/**
 * Render sentiment badge with appropriate styling
 * @param {Object} evt - Sentiment event object
 */
function renderSentimentBadge(evt) {
  const badge = document.getElementById("news-sentiment-badge");
  if (badge) {
    badge.textContent = evt.label;
    // Reset and apply 3D effect classes
    badge.className =
      "inline-flex items-center text-sm font-bold px-4 py-1.5 rounded-full border border-slate-200 transition-all animate-fade-in backdrop-blur-md shadow-[0_4px_12px_rgba(0,0,0,0.1)] ring-1 ring-white/40 dark:ring-white/10";

    const color = evt.color || "gray";
    if (color === "green") {
      badge.classList.add(
        "bg-gradient-to-b",
        "from-emerald-50",
        "to-emerald-100/90",
        "dark:from-emerald-500/10",
        "dark:to-emerald-500/30",
        "text-emerald-700",
        "dark:text-emerald-300",
        "border-emerald-200",
        "dark:border-emerald-500/40",
      );
    } else if (color === "red") {
      badge.classList.add(
        "bg-gradient-to-b",
        "from-rose-50",
        "to-rose-100/90",
        "dark:from-rose-500/10",
        "dark:to-rose-500/30",
        "text-rose-700",
        "dark:text-rose-300",
        "border-rose-200",
        "dark:border-rose-500/40",
      );
    } else if (color === "yellow") {
      badge.classList.add(
        "bg-gradient-to-b",
        "from-amber-50",
        "to-amber-100/90",
        "dark:from-amber-500/10",
        "dark:to-amber-500/30",
        "text-amber-800",
        "dark:text-amber-300",
        "border-amber-200",
        "dark:border-amber-500/40",
      );
    } else if (color === "orange") {
      badge.classList.add(
        "bg-gradient-to-b",
        "from-orange-50",
        "to-orange-100/90",
        "dark:from-orange-500/10",
        "dark:to-orange-500/30",
        "text-orange-700",
        "dark:text-orange-300",
        "border-orange-200",
        "dark:border-orange-500/40",
      );
    } else if (color === "blue") {
      badge.classList.add(
        "bg-gradient-to-b",
        "from-blue-50",
        "to-blue-100/90",
        "dark:from-blue-500/10",
        "dark:to-blue-500/30",
        "text-blue-700",
        "dark:text-blue-300",
        "border-blue-200",
        "dark:border-blue-500/40",
      );
    } else {
      badge.classList.add(
        "bg-gradient-to-b",
        "from-slate-50",
        "to-slate-100/90",
        "dark:from-slate-800/40",
        "dark:to-slate-800/80",
        "text-slate-700",
        "dark:text-slate-300",
        "border-slate-200",
        "dark:border-slate-600",
      );
    }
  }
}

/**
 * Clear news display (called when resetting stock selection)
 */
function clearNewsDisplay() {
  const newsListContainer = document.getElementById("news-list-container");
  if (newsListContainer) newsListContainer.innerHTML = "";
}
