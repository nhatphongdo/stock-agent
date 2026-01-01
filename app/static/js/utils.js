// ===========================================
// CONFIGURATION - All constants in one place
// ===========================================
const CONFIG = {
  // Storage Keys
  STORAGE_KEYS: {
    THEME: "theme",
    CONVERSATION: "trade_agent_conversation",
    USER_NAME: "user_name",
  },
  // Chart Settings
  CHART: {
    CANDLE_MIN_WIDTH: 0,
    CANDLE_MAX_WIDTH: 60,
    SPACING_RATIO: 0.6,
    Y_AXIS_WIDTH: 55,
    ZOOM_SPEED: 0.1,
    MIN_ZOOM_RANGE_DAYS: 5,
  },
  // Colors
  COLORS: {
    UP: "#10b981",
    DOWN: "#ef4444",
    UNCHANGED: "#94a3b8",
    MA: "#3b82f6",
    EMA: "#f97316",
    BB: "#a855f7",
    RSI: "#f59e0b",
    MACD_LINE: "#3b82f6",
    MACD_SIGNAL: "#ef4444",
    MACD_HIST_UP: "#10b981",
    MACD_HIST_DOWN: "#ef4444",
    VOLUME_SMA: "#8b5cf6",
    GRID_LIGHT: "rgba(0,0,0,0.06)",
    GRID_DARK: "rgba(255,255,255,0.06)",
    TEXT_LIGHT: "#64748b",
    TEXT_DARK: "#94a3b8",
    CROSSHAIR: "rgba(148, 163, 184, 0.8)",
    TOOLTIP_BG_LIGHT: "rgba(255, 255, 255, 0.95)",
    TOOLTIP_BG_DARK: "rgba(30, 41, 59, 0.95)",
  },
  // Timeframe mappings
  TIMEFRAME_DAYS: {
    "1D": 1,
    "1W": 7,
  },
  // UI Settings
  UI: {
    RESIZE_MIN_PERCENT: 20,
    RESIZE_MAX_PERCENT: 70,
    TOAST_DURATION_MS: 3000,
  },
};
// Freeze to prevent accidental modifications
Object.freeze(CONFIG);
Object.freeze(CONFIG.STORAGE_KEYS);
Object.freeze(CONFIG.CHART);
Object.freeze(CONFIG.COLORS);
Object.freeze(CONFIG.TIMEFRAME_DAYS);
Object.freeze(CONFIG.UI);

// --- Valid Stock Symbols (fetched from backend) ---
let symbolsMap = {}; // symbol -> {name, exchange}
const VALID_EXCHANGES = ["HOSE", "HNX", "UPCOM", "HSX", "VN30", "HNX30"];

async function fetchValidSymbols() {
  try {
    const response = await fetch("/symbols");
    if (response.ok) {
      const data = await response.json();
      // Filter to cache only valid stocks
      symbolsMap = {};
      for (const [symbol, info] of Object.entries(data.symbols || {})) {
        const exchange = (info?.exchange || "HOSE").toUpperCase();
        if (
          VALID_EXCHANGES.includes(exchange) &&
          ["STOCK", "ETF"].includes(info.type)
        ) {
          symbolsMap[symbol] = info;
        }
      }
    }
  } catch (error) {
    console.error("Failed to fetch stock symbols:", error);
  }
}

// Helper to get stock info
function getStockInfo(symbol) {
  const info = symbolsMap[symbol];
  if (info && typeof info === "object") {
    return {
      name: info.name || symbol,
      exchange: info.exchange || "HOSE",
    };
  }
  // Fallback for old format (string)
  return { name: info || symbol, exchange: "HOSE" };
}

// Fetch symbols on page load
document.addEventListener("DOMContentLoaded", () => {
  fetchValidSymbols();
});

/**
 * Sets up symbol autocomplete for an input element.
 * @param {HTMLInputElement | null} inputEl - The input element.
 * @param {HTMLElement | null} suggestionsEl - The suggestions container element.
 * @param {(symbol: string) => void} onSelect - Callback when a symbol is selected.
 */
function sharedSetupSymbolAutocomplete(inputEl, suggestionsEl, onSelect) {
  if (!inputEl || !suggestionsEl) return;

  inputEl.addEventListener("input", () => {
    const query = inputEl.value.trim().toUpperCase();
    if (!query || query.length < 1) {
      suggestionsEl.classList.add("hidden");
      return;
    }

    // Use symbolsMap (filtered for valid stocks only)
    const matches = Object.entries(symbolsMap)
      .filter(([symbol, info]) => {
        const name = typeof info === "object" ? info.name : info;
        return (
          symbol.includes(query) ||
          (name && name.toLowerCase().includes(query.toLowerCase()))
        );
      })
      .slice(0, 10);

    if (matches.length === 0) {
      suggestionsEl.classList.add("hidden");
      return;
    }

    suggestionsEl.innerHTML = matches
      .map(([symbol, info]) => {
        const name = typeof info === "object" ? info.name : info;
        return `
          <div class="px-4 py-2 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer flex justify-between items-center" data-symbol="${symbol}">
            <span class="font-bold text-emerald-600 dark:text-emerald-400">${symbol}</span>
            <span class="text-xs text-slate-500 truncate ml-2">${
              name || ""
            }</span>
          </div>
        `;
      })
      .join("");

    // Add click handlers for suggestions
    suggestionsEl.querySelectorAll("[data-symbol]").forEach((item) => {
      item.addEventListener("click", () => {
        const symbol = item.getAttribute("data-symbol");
        onSelect(symbol);
        suggestionsEl.classList.add("hidden");
      });
    });

    suggestionsEl.classList.remove("hidden");
  });

  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      const query = inputEl.value.trim().toUpperCase();
      if (query) {
        onSelect(query);
        suggestionsEl.classList.add("hidden");
      }
    }
  });

  // Hide suggestions when clicking outside
  document.addEventListener("click", (e) => {
    const target = /** @type {Node} */ (e.target);
    if (!inputEl.contains(target) && !suggestionsEl.contains(target)) {
      suggestionsEl.classList.add("hidden");
    }
  });
}

/**
 * Gets the initials from a name.
 * @param {string} name - The full name.
 * @returns {string} The initials (e.g., "John Doe" -> "JD").
 */
function getInitials(name) {
  if (!name) return "??";
  const parts = name.split(" ");
  if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

/**
 * Removes skeleton loading classes from an element.
 * @param {string} elementId - The ID of the element to remove skeleton from.
 */
function removeSkeleton(elementId) {
  const el = document.getElementById(elementId);
  if (el) {
    el.classList.remove(
      "skeleton-shimmer",
      "text-transparent",
      "bg-slate-200/50",
      "dark:bg-slate-800/50",
      "bg-slate-200/50",
      "dark:bg-slate-800/40",
    );
  }
}

/**
 * Updates an element's value while preserving its tooltip-content child.
 * @param {string} elementId - The ID of the element to update.
 * @param {string} value - The new value to set.
 */
function updateValueWithTooltip(elementId, value) {
  const el = document.getElementById(elementId);
  if (!el) return;

  // Find and preserve tooltip-content
  const tooltipContent = el.querySelector(".tooltip-content");
  const tooltipHTML = tooltipContent ? tooltipContent.outerHTML : "";

  // Create a text node for the value
  el.innerHTML = value + tooltipHTML;
}

/**
 * Process markdown content with optional stock ticker highlighting.
 * @param {string} text - The text to process.
 * @param {boolean} highlightTickers - Whether to wrap stock symbols in clickable spans (default: true).
 * @returns {string} The processed HTML content.
 */
function processContent(text, highlightTickers = true) {
  let processedText = text;

  // Ensure space after punctuation (., !, ?) if not followed by a space, number, or other punctuation
  // Skip file extensions (dot followed by lowercase letter like .pdf, .xlsx)
  // Add space when dot followed by uppercase letter (new sentence)
  processedText = processedText.replace(/([.])([A-Z])/g, "$1 $2");
  processedText = processedText.replace(/([!?])([A-Za-z])/g, "$1 $2");

  // Parse markdown first
  let html = marked.parse(processedText);

  // Wrap stock tickers in clickable spans (only if highlightTickers is true)
  if (highlightTickers) {
    html = html.replace(/\b([A-Z0-9]{3,10})\b/g, (match, ticker) => {
      // Check against the valid symbols list fetched from backend
      if (ticker in symbolsMap) {
        return `<span class="stock-ticker" data-symbol="${ticker}">${ticker}</span>`;
      }
      return match;
    });
  }

  // Wrap tables in scrollable container
  html = html.replace(
    /<table>/g,
    '<div class="table-outer-container"><div class="table-wrapper"><table>',
  );
  html = html.replace(/<\/table>/g, "</table></div></div>");

  // Post-process: merge cells in rows with only one cell having content
  // This handles note rows at the end of tables
  const tempDiv = document.createElement("div");
  tempDiv.innerHTML = html;
  tempDiv.querySelectorAll("table tr").forEach((row) => {
    const cells = row.querySelectorAll("td");
    if (cells.length > 1) {
      // Count cells with actual content (not empty)
      const nonEmptyCells = Array.from(cells).filter(
        (td) => td.textContent.trim() !== "",
      );
      // If only one cell has content, merge all cells into that one
      if (nonEmptyCells.length === 1) {
        const contentCell = nonEmptyCells[0];
        const content = contentCell.innerHTML;
        const colCount = cells.length;
        // Remove all cells
        cells.forEach((cell) => cell.remove());
        // Create new merged cell
        const newCell = document.createElement("td");
        newCell.setAttribute("colspan", String(colCount));
        newCell.innerHTML = content;
        newCell.style.whiteSpace = "normal";
        newCell.style.fontStyle = "italic";
        newCell.style.color = "#64748b";
        row.appendChild(newCell);
      }
    }
  });
  html = tempDiv.innerHTML;

  return html;
}

/**
 * Wrapper for processContent without stock ticker highlighting.
 * Used for News and Technical Analysis tabs.
 * @param {string} text - The text to process.
 * @returns {string} The processed HTML content.
 */
function processContentNoTickers(text) {
  return processContent(text, false);
}

// Global Tooltip System
(function initGlobalTooltip() {
  const globalTooltip = document.getElementById("global-tooltip");
  if (!globalTooltip) return;

  let showTimeout = null;
  let hideTimeout = null;
  let currentTrigger = null;

  const showTooltip = (trigger) => {
    const content = trigger.querySelector(".tooltip-content");
    if (!content) return;

    globalTooltip.textContent = content.textContent;
    const rect = trigger.getBoundingClientRect();
    let left = rect.left;
    let top = rect.bottom + 8;

    globalTooltip.classList.add("show");
    const tooltipRect = globalTooltip.getBoundingClientRect();

    if (left + tooltipRect.width > window.innerWidth - 10) {
      left = window.innerWidth - tooltipRect.width - 10;
    }
    if (left < 10) left = 10;

    if (top + tooltipRect.height > window.innerHeight - 10) {
      top = rect.top - tooltipRect.height - 8;
      globalTooltip.classList.add("arrow-down");
    } else {
      globalTooltip.classList.remove("arrow-down");
    }

    globalTooltip.style.left = left + "px";
    globalTooltip.style.top = top + "px";
  };

  const hideTooltip = () => {
    globalTooltip.classList.remove("show");
    currentTrigger = null;
  };

  document.addEventListener(
    "mouseover",
    (e) => {
      if (!(e.target instanceof Element)) return;
      const tooltipTrigger = e.target.closest(".indicator-tooltip");

      if (!tooltipTrigger) return;

      // If we're already on this trigger, just stay
      if (currentTrigger === tooltipTrigger) {
        if (hideTimeout) {
          clearTimeout(hideTimeout);
          hideTimeout = null;
        }
        return;
      }

      // New trigger
      if (hideTimeout) {
        clearTimeout(hideTimeout);
        hideTimeout = null;
      }

      if (showTimeout) clearTimeout(showTimeout);

      currentTrigger = tooltipTrigger;
      showTimeout = setTimeout(() => {
        showTooltip(tooltipTrigger);
      }, 200); // 200ms delay to show
    },
    true,
  );

  document.addEventListener(
    "mouseout",
    (e) => {
      if (!(e.target instanceof Element)) return;
      const tooltipTrigger = e.target.closest(".indicator-tooltip");

      if (!tooltipTrigger) return;

      // Check if we are moving to a child of the same trigger
      const relatedTarget = /** @type {Node | null} */ (e.relatedTarget);
      if (relatedTarget && tooltipTrigger.contains(relatedTarget)) {
        return;
      }

      if (showTimeout) {
        clearTimeout(showTimeout);
        showTimeout = null;
      }

      if (hideTimeout) clearTimeout(hideTimeout);
      hideTimeout = setTimeout(() => {
        hideTooltip();
      }, 100); // 100ms delay to hide
    },
    true,
  );
})();

// Theme Management
function setTheme(theme) {
  const themeIconDark = document.getElementById("theme-icon-dark");
  const themeIconLight = document.getElementById("theme-icon-light");
  const html = document.documentElement;

  if (theme === "dark") {
    html.classList.add("dark");
    themeIconDark.classList.add("hidden");
    themeIconLight.classList.remove("hidden");
  } else {
    html.classList.remove("dark");
    themeIconDark.classList.remove("hidden");
    themeIconLight.classList.add("hidden");
  }
  localStorage.setItem("theme", theme);
}

// Check for saved theme or system preference
const savedTheme = localStorage.getItem("theme");
if (savedTheme) {
  setTheme(savedTheme);
} else if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
  setTheme("dark");
}

const themeToggle = document.getElementById("theme-toggle");
themeToggle.addEventListener("click", () => {
  const html = document.documentElement;
  setTheme(html.classList.contains("dark") ? "light" : "dark");
  // Re-render charts with new theme if a stock is selected
  if (currentChartSymbol) {
    initAdvancedChart(currentChartSymbol);
  }
});

/**
 * Format price value to Vietnamese locale
 * @param {number} p - Price value
 * @returns {string} - Formatted price
 */
function formatPrice(p) {
  return p !== null && p !== undefined
    ? p.toLocaleString("vi-VN", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2,
      })
    : "--";
}

/**
 * Format number with decimals
 * @param {number} n - Number value
 * @param {number} decimals - Number of decimal places. If not defined, automatically set to real value (0 if no fraction, 2 if has fraction)
 * @param {boolean} converted - Convert to K, M
 * @returns {string} - Formatted number
 */
function formatNumber(n, decimals = 2, converted = false) {
  if (converted) {
    if (n >= 1000000) {
      return (n / 1000000).toFixed(decimals) + "M";
    } else if (n >= 1000) {
      return (n / 1000).toFixed(decimals) + "K";
    }
    return n.toLocaleString("vi-VN", {
      minimumFractionDigits: decimals ?? 0,
      maximumFractionDigits: decimals ?? 2,
    });
  }
  return n !== null && n !== undefined
    ? n.toLocaleString("vi-VN", {
        minimumFractionDigits: decimals ?? 0,
        maximumFractionDigits: decimals ?? 2,
      })
    : "--";
}

/**
 * Format full date time
 * @param {number | string} timestamp - Timestamp as string or in seconds
 * @returns {string} - Formatted date time
 */
function formatFullDateTime(timestamp) {
  const date =
    typeof timestamp === "string"
      ? new Date(timestamp)
      : new Date(timestamp * 1000);
  return date.toLocaleString("vi-VN", {
    weekday: "long",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Format date
 * @param {string | number} timestamp - Timestamp as string or in seconds
 * @returns {string} - Formatted date
 */
function formatDate(timestamp) {
  const date =
    typeof timestamp === "string"
      ? new Date(timestamp)
      : new Date(timestamp * 1000);
  return date.toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}
