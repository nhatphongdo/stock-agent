// Chart Module - Global chart instances for cleanup (Lightweight Charts)
let priceChart = null;
let candleSeries = null;
let volumeSeries = null;
let indicatorValues = {}; // Store raw indicator values mapping time -> {key: value}
let indicatorConfigs = {}; // Store indicator config mapping indicator key -> config
let indicatorSeriesMap = new Map(); // Map indicator key -> array of series
let indicatorDropdownInitialized = false;
let currentChartSymbol = null;
let currentChartStart = null; // Current chart start date (YYYY-MM-DD)
let currentChartEnd = null; // Current chart end date (YYYY-MM-DD)

// Analysis method dropdown state
let analysisMethodDropdownInitialized = false;
let currentAnalysisMethod = null; // Currently selected method ID
let analysisMethodMarkers = []; // Store visualization primitives
let methodIndicatorValues = {}; // Store raw values for analysis method indicators
let methodIndicatorConfigs = {}; // Store configs for analysis method indicators
let activeSignalMarkers = []; // Store current signal markers for hover detection

// Store available symbols from latest analysis
let availableAnalysisSymbols = [];
let symbolSelectorInitialized = false;

// Current timeframe and interval values
let currentTimeframe = "1Y";
let currentInterval = "1D";
let timeframeDropdownInitialized = false;
let intervalDropdownInitialized = false;

// Auto-reload state
let autoReloadEnabled = false;
let autoReloadIntervalId = null;
const AUTO_RELOAD_INTERVAL_MS = 1 * 60 * 1000; // every minute

/**
 * Render symbol list items based on search filter
 * @param {string} filter - Search filter string
 */
function renderSymbolList(filter = "") {
  const listContainer = document.getElementById("chart-symbol-list");
  if (!listContainer) return;

  const filtered = availableAnalysisSymbols
    .filter((s) => s.toUpperCase().includes(filter.toUpperCase()))
    .sort((a, b) => a.localeCompare(b));

  if (filtered.length === 0) {
    listContainer.innerHTML =
      '<div class="text-xs text-slate-400 text-center py-2">Không tìm thấy</div>';
    return;
  }

  listContainer.innerHTML = filtered
    .map(
      (symbol) => `
      <div
        class="symbol-item px-2 py-1.5 text-xs font-bold rounded-lg cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 ${
          symbol === currentChartSymbol
            ? "bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400"
            : "text-slate-700 dark:text-slate-300"
        }"
        data-symbol="${symbol}"
      >
        ${symbol}
      </div>
    `,
    )
    .join("");

  // Add click handlers
  listContainer.querySelectorAll(".symbol-item").forEach((item) => {
    item.addEventListener("click", () => {
      const symbol = /** @type {HTMLElement} */ (item).dataset.symbol;
      if (symbol && symbol !== currentChartSymbol) {
        selectStock(symbol);
      }
      // Close dropdown
      const panel = document.getElementById("chart-symbol-selector-panel");
      const chevron = document.getElementById("chart-symbol-chevron");
      if (panel) panel.classList.add("hidden");
      if (chevron) chevron.style.transform = "rotate(0deg)";
    });
  });
}

/**
 * Update the symbol selector dropdown with analyzed symbols
 * @param {string[]} symbols - Array of ticker symbols
 */
function updateChartSymbolSelector(symbols) {
  // Sort symbols ascending
  availableAnalysisSymbols = (symbols || []).sort((a, b) => a.localeCompare(b));
  const container = document.getElementById("chart-symbol-selector-container");
  const valueDisplay = document.getElementById("chart-symbol-selector-value");

  if (!container || !symbols || symbols.length === 0) {
    if (container) container.classList.add("hidden");
    return;
  }

  // Update value display
  if (valueDisplay) {
    valueDisplay.textContent =
      currentChartSymbol || availableAnalysisSymbols[0] || "--";
  }

  // Render initial list
  renderSymbolList();

  // Show the selector
  container.classList.remove("hidden");
  container.classList.add("flex");
}

/**
 * Initialize symbol selector event handlers
 */
function initChartSymbolSelector() {
  if (symbolSelectorInitialized) return;

  const container = document.getElementById("chart-symbol-selector-container");
  const trigger = document.getElementById("chart-symbol-selector-trigger");
  const panel = document.getElementById("chart-symbol-selector-panel");
  const chevron = document.getElementById("chart-symbol-chevron");
  const searchInput = /** @type {HTMLInputElement | null} */ (
    document.getElementById("chart-symbol-search")
  );

  if (!trigger || !panel) return;

  symbolSelectorInitialized = true;

  // Toggle dropdown
  trigger.addEventListener("click", (e) => {
    e.stopPropagation();
    const isHidden = panel.classList.toggle("hidden");
    if (!isHidden) {
      closeAllDropdowns("chart-symbol-selector-panel");
      chevron.style.transform = "rotate(180deg)";
      // Focus search input
      if (searchInput) {
        searchInput.value = "";
        searchInput.focus();
        renderSymbolList();
      }
      updateDropdownPosition(trigger, panel);
    } else {
      chevron.style.transform = "rotate(0deg)";
    }
  });

  // Search input handler
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      renderSymbolList(/** @type {HTMLInputElement} */ (e.target).value);
    });
    // Prevent closing when clicking in search
    searchInput.addEventListener("click", (e) => e.stopPropagation());
  }

  // Close when clicking outside
  document.addEventListener("click", (e) => {
    if (container && !container.contains(/** @type {Node} */ (e.target))) {
      panel.classList.add("hidden");
      if (chevron) chevron.style.transform = "rotate(0deg)";
    }
  });
}

/**
 * Initialize Timeframe custom dropdown
 */
function initTimeframeDropdown() {
  if (timeframeDropdownInitialized) return;

  const container = document.getElementById("chart-timeframe-container");
  const trigger = document.getElementById("chart-timeframe-trigger");
  const panel = document.getElementById("chart-timeframe-panel");
  const chevron = document.getElementById("chart-timeframe-chevron");
  const valueDisplay = document.getElementById("chart-timeframe-value");

  if (!trigger || !panel) return;

  timeframeDropdownInitialized = true;

  // Toggle dropdown
  trigger.addEventListener("click", (e) => {
    e.stopPropagation();
    const isHidden = panel.classList.toggle("hidden");
    if (!isHidden) {
      closeAllDropdowns("chart-timeframe-panel");
      if (chevron) chevron.style.transform = "rotate(180deg)";
      updateDropdownPosition(trigger, panel);
    } else {
      if (chevron) chevron.style.transform = "rotate(0deg)";
    }
  });

  // Item click handlers
  panel.querySelectorAll(".timeframe-item").forEach((item) => {
    item.addEventListener("click", () => {
      const value = /** @type {HTMLElement} */ (item).dataset.value;
      const label = item.textContent?.trim();
      if (!value) return;

      currentTimeframe = value;
      if (valueDisplay) valueDisplay.textContent = label || value;

      // Update selection styling
      panel.querySelectorAll(".timeframe-item").forEach((i) => {
        i.classList.remove(
          "bg-primary-100",
          "dark:bg-primary-900/30",
          "text-primary-600",
          "dark:text-primary-400",
        );
        i.classList.add("text-slate-700", "dark:text-slate-300");
      });
      item.classList.add(
        "bg-primary-100",
        "dark:bg-primary-900/30",
        "text-primary-600",
        "dark:text-primary-400",
      );
      item.classList.remove("text-slate-700", "dark:text-slate-300");

      // Close and re-render
      panel.classList.add("hidden");
      if (chevron) chevron.style.transform = "rotate(0deg)";

      clearAllPatternVisualizations();
      clearPatternListUI();
      indicatorSeriesMap.clear();
      renderAdvancedChart(
        currentChartSymbol,
        currentTimeframe,
        currentInterval,
      );

      // Restart auto-reload with new timeframe (if enabled)
      if (autoReloadEnabled) {
        startAutoReload();
      }
    });
  });

  // Close when clicking outside
  document.addEventListener("click", (e) => {
    if (container && !container.contains(/** @type {Node} */ (e.target))) {
      panel.classList.add("hidden");
      if (chevron) chevron.style.transform = "rotate(0deg)";
    }
  });
}

/**
 * Initialize Interval custom dropdown
 */
function initIntervalDropdown() {
  if (intervalDropdownInitialized) return;

  const container = document.getElementById("chart-interval-container");
  const trigger = document.getElementById("chart-interval-trigger");
  const panel = document.getElementById("chart-interval-panel");
  const chevron = document.getElementById("chart-interval-chevron");
  const valueDisplay = document.getElementById("chart-interval-value");

  if (!trigger || !panel) return;

  intervalDropdownInitialized = true;

  // Toggle dropdown
  trigger.addEventListener("click", (e) => {
    e.stopPropagation();
    const isHidden = panel.classList.toggle("hidden");
    if (!isHidden) {
      closeAllDropdowns("chart-interval-panel");
      if (chevron) chevron.style.transform = "rotate(180deg)";
      updateDropdownPosition(trigger, panel);
    } else {
      if (chevron) chevron.style.transform = "rotate(0deg)";
    }
  });

  // Item click handlers
  panel.querySelectorAll(".interval-item").forEach((item) => {
    item.addEventListener("click", () => {
      const value = /** @type {HTMLElement} */ (item).dataset.value;
      const label = item.textContent?.trim();
      if (!value) return;

      currentInterval = value;
      if (valueDisplay) valueDisplay.textContent = label || value;

      // Update selection styling
      panel.querySelectorAll(".interval-item").forEach((i) => {
        i.classList.remove(
          "bg-primary-100",
          "dark:bg-primary-900/30",
          "text-primary-600",
          "dark:text-primary-400",
        );
        i.classList.add("text-slate-700", "dark:text-slate-300");
      });
      item.classList.add(
        "bg-primary-100",
        "dark:bg-primary-900/30",
        "text-primary-600",
        "dark:text-primary-400",
      );
      item.classList.remove("text-slate-700", "dark:text-slate-300");

      // Close and re-render
      panel.classList.add("hidden");
      if (chevron) chevron.style.transform = "rotate(0deg)";

      clearAllPatternVisualizations();
      clearPatternListUI();
      indicatorSeriesMap.clear();
      renderAdvancedChart(
        currentChartSymbol,
        currentTimeframe,
        currentInterval,
      );

      // Restart auto-reload with new interval (if enabled)
      if (autoReloadEnabled) {
        startAutoReload();
      }
    });
  });

  // Close when clicking outside
  document.addEventListener("click", (e) => {
    if (container && !container.contains(/** @type {Node} */ (e.target))) {
      panel.classList.add("hidden");
      if (chevron) chevron.style.transform = "rotate(0deg)";
    }
  });
}

// Refresh charts by fitting content to time scale
function refreshCharts() {
  if (typeof priceChart !== "undefined" && priceChart) {
    const isDark = document.documentElement.classList.contains("dark");
    const theme = isDark ? CONFIG.CHART_THEMES.dark : CONFIG.CHART_THEMES.light;
    priceChart.applyOptions(theme);
    priceChart.timeScale().fitContent();
  }
}

// Update dropdown position to prevent overflow
function updateDropdownPosition(trigger, panel) {
  if (!trigger || !panel) return;

  // Reset to default to measure correctly
  panel.classList.remove("right-0");
  panel.classList.add("left-0");

  const triggerRect = trigger.getBoundingClientRect();
  const panelWidth = panel.offsetWidth || 320;
  const windowWidth = window.innerWidth;

  // Check if dropdown overflows right side of screen
  if (triggerRect.left + panelWidth > windowWidth - 20) {
    // 20px buffer
    panel.classList.remove("left-0");
    panel.classList.add("right-0");
  } else {
    panel.classList.remove("right-0");
    panel.classList.add("left-0");
  }
}

// Close all dropdowns except the specified one
function closeAllDropdowns(exceptId = null) {
  const dropdowns = [
    { panelId: "indicator-dropdown-panel", chevronId: "indicator-chevron" },
    { panelId: "pattern-dropdown-panel", chevronId: "pattern-chevron" },
    {
      panelId: "chart-pattern-dropdown-panel",
      chevronId: null,
      triggerId: "chart-pattern-dropdown-trigger",
    },
    {
      panelId: "sr-zone-dropdown-panel",
      chevronId: null,
      triggerId: "sr-zone-dropdown-trigger",
    },
    {
      panelId: "analysis-method-dropdown-panel",
      chevronId: null,
      triggerId: "analysis-method-dropdown-trigger",
    },
    {
      panelId: "chart-symbol-selector-panel",
      chevronId: "chart-symbol-chevron",
    },
    {
      panelId: "chart-timeframe-panel",
      chevronId: "chart-timeframe-chevron",
    },
    {
      panelId: "chart-interval-panel",
      chevronId: "chart-interval-chevron",
    },
  ];

  dropdowns.forEach((d) => {
    if (d.panelId !== exceptId) {
      const panel = document.getElementById(d.panelId);
      if (panel && !panel.classList.contains("hidden")) {
        panel.classList.add("hidden");

        // Reset chevron
        if (d.chevronId) {
          const chevron = document.getElementById(d.chevronId);
          if (chevron) chevron.classList.remove("rotate-180");
          if (chevron) chevron.style.transform = "rotate(0deg)"; // Handle both class and style rotations used in code
        } else if (d.triggerId) {
          const trigger = document.getElementById(d.triggerId);
          const chevron = /** @type {HTMLElement | null} */ (
            trigger?.querySelector('[data-lucide="chevron-down"]')
          );
          if (chevron) chevron.style.transform = "rotate(0deg)";
        }
      }
    }
  });
}

// Initialize indicator dropdown toggle
function initIndicatorDropdown() {
  if (indicatorDropdownInitialized) return;

  const trigger = document.getElementById("indicator-dropdown-trigger");
  const panel = document.getElementById("indicator-dropdown-panel");
  const chevron = document.getElementById("indicator-chevron");

  if (!trigger || !panel) return;

  // Render Dynamic Content
  renderDynamicIndicators();

  // Helper to render indicators
  async function renderDynamicIndicators() {
    const listContainer = document.getElementById("indicator-list-container");
    if (!listContainer) return;

    // Show loading state
    listContainer.innerHTML =
      '<div class="p-4 text-center text-xs text-slate-500">Đang tải danh sách chỉ báo...</div>';

    const data = await fetchAvailableIndicators();
    if (!data || !data.indicators) {
      listContainer.innerHTML =
        '<div class="p-4 text-center text-xs text-red-500">Không thể tải danh sách chỉ báo</div>';
      return;
    }

    const html = generateIndicatorDropdownHTML(data.indicators, "");
    listContainer.innerHTML = html;

    // Setup search filtering
    const searchInput = /** @type {HTMLInputElement | null} */ (
      document.getElementById("indicator-search")
    );
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        const query = /** @type {HTMLInputElement} */ (e.target).value
          .toLowerCase()
          .trim();
        filterIndicatorList(panel, query);
      });
    }
  }

  /**
   * Filter indicator list based on search query
   * @param {HTMLElement} panel - The dropdown panel element
   * @param {string} query - The search query string
   */
  function filterIndicatorList(panel, query) {
    const items = panel.querySelectorAll(".indicator-item");
    const categories = panel.querySelectorAll(".indicator-category");

    // Show all items if query is empty
    if (!query) {
      items.forEach((item) => {
        /** @type {HTMLElement} */ (item).style.display = "";
      });
      categories.forEach((cat) => {
        /** @type {HTMLElement} */ (cat).style.display = "";
      });
      return;
    }

    // Filter items
    items.forEach((item) => {
      const searchText = item.getAttribute("data-search") || "";
      const matches = searchText.includes(query);
      /** @type {HTMLElement} */ (item).style.display = matches ? "" : "none";
    });

    // Hide categories with no visible items
    categories.forEach((cat) => {
      const visibleItems = cat.querySelectorAll(
        '.indicator-item:not([style*="display: none"])',
      );
      /** @type {HTMLElement} */ (cat).style.display =
        visibleItems.length > 0 ? "" : "none";
    });
  }

  // Toggle dropdown on button click
  trigger.addEventListener("click", (e) => {
    e.stopPropagation();
    const isOpen = !panel.classList.contains("hidden");

    // Close others if we are opening
    if (!isOpen) {
      closeAllDropdowns("indicator-dropdown-panel");
    }

    panel.classList.toggle("hidden");
    chevron?.classList.toggle("rotate-180", !isOpen);
    if (isOpen) {
      updateDropdownPosition(trigger, panel);
    }
  });

  // Close dropdown when clicking outside
  document.addEventListener("click", (e) => {
    const target = /** @type {Node} */ (e.target);
    if (!panel.contains(target) && !trigger.contains(target)) {
      panel.classList.add("hidden");
      chevron?.classList.remove("rotate-180");
    }
  });

  // Update badge count
  const updateBadge = () => {
    const badge = document.getElementById("indicator-count-badge");
    const count = panel.querySelectorAll(
      'input[type="checkbox"]:checked',
    ).length;

    if (badge) {
      badge.textContent = count.toString();
      badge.classList.toggle("hidden", count === 0);
    }
  };

  // Delegated event listener for all indicator checkboxes
  panel.addEventListener("change", (e) => {
    const target = /** @type {HTMLElement} */ (e.target);
    if (target && target.classList.contains("indicator-checkbox")) {
      const checkbox = /** @type {HTMLInputElement} */ (target);
      updateBadge();
      toggleIndicator();
    }
  });

  indicatorDropdownInitialized = true;
}

// Flag to track if expand button has been initialized
let chartExpandInitialized = false;

// Initialize chart expand/fullscreen button
function initChartExpandButton() {
  // Skip if already initialized
  if (chartExpandInitialized) return;

  const expandBtn = document.getElementById("chart-expand-btn");
  const chartTabContent = document.getElementById("tab-content-chart");

  if (!expandBtn || !chartTabContent) return;

  // Mark as initialized
  chartExpandInitialized = true;

  // Placeholder for restoring position
  const placeholderComment = document.createComment("chart-placeholder");

  const toggleFullscreen = () => {
    const isFullscreen = chartTabContent.classList.toggle("chart-fullscreen");
    const icon = document.getElementById("chart-expand-icon");

    if (isFullscreen) {
      // Enter Fullscreen: Move to body
      expandBtn.title = "Thu nhỏ biểu đồ";
      if (icon) {
        icon.setAttribute("data-lucide", "minimize-2");
        lucide.createIcons();
      }

      // Insert placeholder and move element to body
      chartTabContent.parentNode?.insertBefore(
        placeholderComment,
        chartTabContent,
      );
      document.body.appendChild(chartTabContent);
    } else {
      // Exit Fullscreen: Move back to original position
      expandBtn.title = "Mở rộng biểu đồ";
      if (icon) {
        icon.setAttribute("data-lucide", "maximize-2");
        lucide.createIcons();
      }

      // Move back to placeholder
      if (placeholderComment.parentNode) {
        placeholderComment.parentNode.insertBefore(
          chartTabContent,
          placeholderComment,
        );
        placeholderComment.remove();
      }
    }

    // Trigger refresh for charts after layout change
    setTimeout(() => {
      refreshCharts();
    }, 100);
  };

  expandBtn.addEventListener("click", toggleFullscreen);

  // Handle Escape key to exit fullscreen
  document.addEventListener("keydown", (e) => {
    if (
      e.key === "Escape" &&
      chartTabContent.classList.contains("chart-fullscreen")
    ) {
      toggleFullscreen();
    }
  });
}

// Initialize auto-reload toggle button
function initAutoReloadToggle() {
  const toggle = document.getElementById("chart-auto-reload-toggle");
  if (!toggle) return;

  toggle.addEventListener("click", () => {
    autoReloadEnabled = !autoReloadEnabled;
    toggle.setAttribute("aria-pressed", autoReloadEnabled.toString());

    if (autoReloadEnabled) {
      startAutoReload();
    } else {
      stopAutoReload();
    }
  });
}

// Start auto-reload interval
function startAutoReload() {
  stopAutoReload(); // Clear any existing interval
  if (!autoReloadEnabled || !currentChartSymbol) return;

  autoReloadIntervalId = setInterval(() => {
    if (autoReloadEnabled && currentChartSymbol) {
      fetchAndUpdateChartData();
    }
  }, AUTO_RELOAD_INTERVAL_MS);
}

// Stop auto-reload interval
function stopAutoReload() {
  if (autoReloadIntervalId) {
    clearInterval(autoReloadIntervalId);
    autoReloadIntervalId = null;
  }
}

// Fetch and update chart data without re-rendering the entire chart
async function fetchAndUpdateChartData() {
  if (!priceChart || !candleSeries || !volumeSeries || !currentChartSymbol) {
    return;
  }

  try {
    const response = await fetch(
      `/chart/${currentChartSymbol}?start=${currentChartStart}&end=${currentChartEnd}&interval=${currentInterval}`,
    );

    if (!response.ok) {
      console.warn("Auto-reload: Failed to fetch chart data");
      return;
    }

    const result = await response.json();

    // Convert API data to chart format
    const data = result.data.map((d) => ({
      x: new Date(d.time),
      o: d.open,
      h: d.high,
      l: d.low,
      c: d.close,
      v: d.volume,
    }));

    // Convert to Lightweight Charts format
    const chartData = data.map((d) => ({
      time: Math.floor(d.x.getTime() / 1000),
      open: d.o,
      high: d.h,
      low: d.l,
      close: d.c,
    }));

    const volumeData = data.map((d) => ({
      time: Math.floor(d.x.getTime() / 1000),
      value: d.v,
      color: d.c >= d.o ? "rgba(16, 185, 129, 0.6)" : "rgba(239, 68, 68, 0.6)",
    }));

    // Update series data (preserves indicators and patterns)
    candleSeries.setData(chartData);
    volumeSeries.setData(volumeData);
  } catch (err) {
    console.warn("Auto-reload: Error fetching chart data", err);
  }
}

// Trigger chart display and initialization
function triggerChartDisplay(symbol) {
  document.getElementById("chart-tab-content-empty").classList.add("hidden");
  document
    .getElementById("chart-tab-content-container")
    .classList.remove("hidden");

  // Initialize dropdown and expand button after container is visible
  initIndicatorDropdown();
  initChartExpandButton();
  initAutoReloadToggle();
  initChartSymbolSelector();
  initTimeframeDropdown();
  initIntervalDropdown();
  initPatternDropdown();
  initChartPatternDropdown();
  initSRZoneDropdown();
  initAnalysisMethodDropdown();

  initAdvancedChart(symbol);
}

// Initialize Advanced Chart
function initAdvancedChart(symbol) {
  currentChartSymbol = symbol;

  // Update symbol selector display value
  const valueDisplay = document.getElementById("chart-symbol-selector-value");
  if (valueDisplay) {
    valueDisplay.textContent = symbol;
  }
  // Re-render list to update selection state
  renderSymbolList();

  // Clear pattern markers when switching symbols
  displayedPatternMarkers.clear();
  markersPrimitive = null;

  // Clear data when switching symbols
  indicatorSeriesMap.clear();

  // Clear analysis method data
  methodIndicatorValues = {};
  methodIndicatorConfigs = {};
  activeSignalMarkers = [];

  // Clear pattern list UI
  clearPatternListUI();

  // Use state variables for timeframe and interval
  renderAdvancedChart(symbol, currentTimeframe, currentInterval);

  // Enable auto-reload by default when selecting a new symbol
  autoReloadEnabled = true;
  const toggle = document.getElementById("chart-auto-reload-toggle");
  if (toggle) {
    toggle.setAttribute("aria-pressed", "true");
  }
  startAutoReload();
}

/**
 * Handle indicator checkbox change - clear and reload all indicators
 * Uses batch API pattern from chart-indicator.js
 */
function toggleIndicator() {
  // If chart is not available, fall back to full re-render
  if (!priceChart) {
    renderAdvancedChart(currentChartSymbol, currentTimeframe, currentInterval);
    return;
  }

  // Use batch pattern: clear all and reload all selected
  handleIndicatorChange({
    chart: priceChart,
    candleSeries,
    seriesMap: indicatorSeriesMap,
    indicatorValues,
    indicatorConfigs,
    symbol: currentChartSymbol,
    start: currentChartStart,
    end: currentChartEnd,
    interval: currentInterval,
    panelSelector: "#indicator-dropdown-panel",
  });
}

// Helper to check if indicator is enabled
function isIndicatorEnabled(indicatorId) {
  const el = /** @type {HTMLInputElement | null} */ (
    document.getElementById(indicatorId)
  );
  return el?.checked || false;
}

// Render chart with multiple panes (async - fetches real data from API)
async function renderAdvancedChart(symbol, timeframe, interval) {
  const chartContainer = document.getElementById("chart-container");
  if (!chartContainer) return;

  // Destroy previous instance
  if (priceChart) {
    priceChart.remove();
    priceChart = null;
  }
  candleSeries = null;
  volumeSeries = null;
  indicatorValues = {};
  indicatorConfigs = {};
  indicatorSeriesMap.clear();

  // Calculate date range from timeframe
  const end = new Date();
  const start = new Date();
  if (timeframe.endsWith("M")) {
    start.setMonth(start.getMonth() - parseInt(timeframe));
  } else if (timeframe.endsWith("Y")) {
    start.setFullYear(start.getFullYear() - parseInt(timeframe));
  } else {
    start.setDate(start.getDate() - (CONFIG.TIMEFRAME_DAYS[timeframe] || 30));
  }

  const formatDate = (d) => d.toISOString().split("T")[0];
  // Store global chart date range for pattern APIs
  currentChartStart = formatDate(start);
  currentChartEnd = formatDate(end);

  // Interval is passed directly to API (ONE_MINUTE, ONE_DAY)
  const apiInterval = interval;

  // Get skeleton from template
  const skeletonTemplate = /** @type {HTMLTemplateElement | null} */ (
    document.getElementById("chart-skeleton-template")
  );
  if (skeletonTemplate) {
    // Clone template and add dynamic bars
    const skeletonContent = /** @type {DocumentFragment} */ (
      skeletonTemplate.content.cloneNode(true)
    );
    const barsContainer = skeletonContent.querySelector(".chart-skeleton-bars");
    if (barsContainer) {
      for (let i = 0; i < 20; i++) {
        const bar = document.createElement("div");
        bar.className =
          "flex-1 inset-0 bg-slate-200/50 dark:bg-slate-800/40 skeleton-shimmer-vertical rounded";
        bar.style.height = `${30 + Math.random() * 60}%`;
        barsContainer.appendChild(bar);
      }
    }

    chartContainer.innerHTML = "";
    chartContainer.append(skeletonContent.children[0]);
  }

  let chartData;
  try {
    const response = await fetch(
      `/chart/${symbol}?start=${currentChartStart}&end=${currentChartEnd}&interval=${apiInterval}`,
    );
    if (response.ok) {
      const result = await response.json();
      // Convert data to Lightweight Charts format (Unix timestamp in seconds)
      chartData = result.data.map((d) => ({
        ...d,
        time: Math.floor(new Date(d.time).getTime() / 1000),
      }));
    } else {
      throw new Error("API error");
    }
  } catch (err) {
    console.error("Chart API error:", err);
    // Show error message with links to external charts
    const stockInfo = getStockInfo(symbol);
    const exchange = stockInfo?.exchange || "HOSE";
    const errorTemplate = /** @type {HTMLTemplateElement | null} */ (
      document.getElementById("chart-error-template")
    );
    if (errorTemplate) {
      const errorContent = /** @type {DocumentFragment} */ (
        errorTemplate.content.cloneNode(true)
      );
      const symbolEl = errorContent.querySelector(".chart-error-symbol");
      const tradingViewLink = /** @type {HTMLAnchorElement | null} */ (
        errorContent.querySelector(".chart-error-tradingview")
      );
      const investingLink = /** @type {HTMLAnchorElement | null} */ (
        errorContent.querySelector(".chart-error-investing")
      );
      if (symbolEl) symbolEl.textContent = symbol;
      if (tradingViewLink)
        tradingViewLink.href = `https://www.tradingview.com/chart/?symbol=${exchange}:${symbol}`;
      if (investingLink)
        investingLink.href = `https://vn.investing.com/search?q=${symbol}`;
      chartContainer.innerHTML = "";
      chartContainer.appendChild(errorContent);
    }
    lucide.createIcons();
    return; // Exit early, don't try to render chart
  }

  // Show chart, remove skeletons
  chartContainer.innerHTML = "";
  const isDark = document.documentElement.classList.contains("dark");
  const theme = isDark ? CONFIG.CHART_THEMES.dark : CONFIG.CHART_THEMES.light;

  // Create single chart with pane support
  priceChart = LightweightCharts.createChart(chartContainer, {
    autoSize: true,
    ...theme,
    timeScale: {
      ...theme.timeScale,
      timeVisible: apiInterval.includes("m") || apiInterval === "1H",
      secondsVisible: false,
    },
  });

  const volumeData = chartData.map((d) => ({
    time: d.time,
    value: d.volume,
    color:
      d.close >= d.open ? "rgba(16, 185, 129, 0.6)" : "rgba(239, 68, 68, 0.6)",
  }));

  // Add Candlestick Series
  candleSeries = priceChart.addSeries(
    LightweightCharts.CandlestickSeries,
    {
      priceFormat: {
        type: "custom",
        formatter: (price) => formatNumber(price, 0),
      },
      upColor: CONFIG.COLORS.UP,
      downColor: CONFIG.COLORS.DOWN,
      borderUpColor: CONFIG.COLORS.UP,
      borderDownColor: CONFIG.COLORS.DOWN,
      wickUpColor: CONFIG.COLORS.UP,
      wickDownColor: CONFIG.COLORS.DOWN,
    },
    0,
  );
  candleSeries.setData(chartData);

  // Add Volume Series (Histogram) in a separate pane (paneIndex: 1)
  volumeSeries = priceChart.addSeries(
    LightweightCharts.HistogramSeries,
    {
      priceFormat: { type: "volume" },
    },
    1,
  ); // paneIndex 1 = second pane for volume
  volumeSeries.setData(volumeData);

  // Configure volume pane height ratio (approximately 30% for volume)
  priceChart.panes()[1]?.setHeight(150);

  // =====================
  // ADD ENABLED INDICATORS (Batch Load)
  // =====================
  handleIndicatorChange({
    chart: priceChart,
    candleSeries,
    seriesMap: indicatorSeriesMap,
    indicatorValues,
    indicatorConfigs,
    symbol,
    start: currentChartStart,
    end: currentChartEnd,
    interval,
    panelSelector: "#indicator-dropdown-panel",
  });

  // Create tooltip using shared utility
  const chartTooltip = createChartTooltip(chartContainer);

  // Single crosshair handler for unified chart with panes
  priceChart.subscribeCrosshairMove((param) => {
    if (param.time && param.point) {
      // Get candle data
      const candlePrice = /** @type {ICandleData | undefined} */ (
        param.seriesData.get(candleSeries)
      );
      // Get volume data
      const volData = /** @type {IVolumeData | undefined} */ (
        param.seriesData.get(volumeSeries)
      );

      let tooltipContent = `<div style="margin-bottom: 6px; font-weight: 500; opacity: 0.8;">${formatFullDateTime(
        param.time,
      )}</div>`;

      if (candlePrice) {
        const changePercent = (
          ((candlePrice.close - candlePrice.open) / candlePrice.open) *
          100
        ).toFixed(2);
        const changeColor =
          candlePrice.close >= candlePrice.open ? "#10b981" : "#ef4444";
        const changeSign = candlePrice.close >= candlePrice.open ? "+" : "";
        tooltipContent += `
          <div><span style="opacity: 0.6;">Open:</span> <strong>${formatPrice(
            candlePrice.open,
          )}</strong></div>
          <div><span style="opacity: 0.6;">High:</span> <strong>${formatPrice(
            candlePrice.high,
          )}</strong></div>
          <div><span style="opacity: 0.6;">Low:</span> <strong>${formatPrice(
            candlePrice.low,
          )}</strong></div>
          <div><span style="opacity: 0.6;">Close:</span> <strong>${formatPrice(
            candlePrice.close,
          )}</strong> <span style="color: ${changeColor};">(${changeSign}${changePercent}%)</span></div>
        `;
      }

      if (volData) {
        tooltipContent += `<div><span style="opacity: 0.6;">Volume:</span> <strong>${formatNumber(
          volData.value,
          0,
        )}</strong></div>`;
      }

      // Add indicator values using shared utility (MERGE standard + method indicators)
      const mergedValues = {
        ...(indicatorValues[param.time] || {}),
        ...(methodIndicatorValues[param.time] || {}),
      };
      const mergedConfigs = {
        ...indicatorConfigs,
        ...methodIndicatorConfigs,
      };

      tooltipContent += renderTooltipIndicators(mergedValues, mergedConfigs);

      // Add signal marker info if hovering on a marker
      const markerAtTime = activeSignalMarkers.find(
        (m) => m.time === param.time,
      );
      if (markerAtTime) {
        const directionIcon = markerAtTime.direction === "up" ? "🟢" : "🔴";
        const directionText = markerAtTime.direction === "up" ? "Mua" : "Bán";
        tooltipContent += `
          <div style="border-top: 1px solid rgba(128,128,128,0.3); margin-top: 6px; padding-top: 6px;">
            <div style="font-weight: bold; margin-bottom: 2px;">${
              markerAtTime.methodName
            }</div>
            <div>${directionIcon} <strong>${
              markerAtTime.type
            }</strong> (${directionText})</div>
            <div style="font-size: 11px; opacity: 0.8;">Giá: ${formatPrice(
              markerAtTime.price,
            )}</div>
          </div>`;
      }

      chartTooltip.innerHTML = tooltipContent;
      chartTooltip.style.display = "block";
      // Apply theme using shared utility
      applyTooltipTheme(chartTooltip);

      updateTooltipPosition(chartTooltip, chartContainer, param);
    } else {
      chartTooltip.style.display = "none";
    }
  });

  setTimeout(() => {
    refreshCharts();
  }, 50);
}

// --- Pattern Recognition Logic ---

let patternDropdownInitialized = false;
/** @type {Map<string, object>} Store current markers by pattern key (date_name) */
let displayedPatternMarkers = new Map();
/** @type {object|null} Store the markers primitive reference for removal */
let markersPrimitive = null;

function initPatternDropdown() {
  // Skip if already initialized
  if (patternDropdownInitialized) return;

  const trigger = document.getElementById("pattern-dropdown-trigger");
  const panel = document.getElementById("pattern-dropdown-panel");
  const chevron = document.getElementById("pattern-chevron");
  const container = document.getElementById("pattern-dropdown-container");
  const scanBtn = document.getElementById("scan-pattern-btn");

  if (!trigger || !panel) return;

  patternDropdownInitialized = true;

  trigger.addEventListener("click", (e) => {
    e.stopPropagation();

    // Close others if we are opening
    if (panel.classList.contains("hidden")) {
      closeAllDropdowns("pattern-dropdown-panel");
    }

    const isHidden = panel.classList.toggle("hidden");
    if (!isHidden) {
      chevron.style.transform = "rotate(180deg)";
      updateDropdownPosition(trigger, panel);

      // Auto scan if empty or first open
      const listContainer = document.getElementById("pattern-list-container");
      if (listContainer.children.length <= 1 && currentChartSymbol) {
        fetchPatterns(currentChartSymbol);
      }
    } else {
      chevron.style.transform = "rotate(0deg)";
    }
  });

  // Close when clicking outside
  document.addEventListener("click", (e) => {
    if (e.target instanceof Node && !container.contains(e.target)) {
      panel.classList.add("hidden");
      chevron.style.transform = "rotate(0deg)";
    }
  });

  // Prevent closing when clicking inside panel
  panel.addEventListener("click", (e) => {
    e.stopPropagation();
  });

  if (scanBtn) {
    scanBtn.addEventListener("click", () => {
      if (currentChartSymbol) {
        fetchPatterns(currentChartSymbol);
      }
    });
  }
}

async function fetchPatterns(symbol) {
  const listContainer = document.getElementById("pattern-list-container");
  const badge = document.getElementById("pattern-count-badge");

  const spinnerTemplate = /** @type {HTMLTemplateElement} */ (
    document.getElementById("loading-spinner-template")
  );
  listContainer.innerHTML = "";
  listContainer.appendChild(spinnerTemplate.content.cloneNode(true));

  try {
    const intervalEl = /** @type {HTMLSelectElement} */ (
      document.getElementById("chart-interval")
    );
    const interval = intervalEl ? intervalEl.value : "1D";
    const response = await fetch(
      `/candle-patterns/${symbol}?start=${currentChartStart}&end=${currentChartEnd}&interval=${interval}`,
    );

    const data = await response.json();

    if (data.error) {
      const errorTemplate = /** @type {HTMLTemplateElement} */ (
        document.getElementById("text-error-template")
      );
      const errorEl = /** @type {HTMLElement} */ (
        errorTemplate.content.cloneNode(true)
      ).firstElementChild;
      errorEl.textContent = data.error;
      listContainer.innerHTML = "";
      listContainer.appendChild(errorEl);
      return;
    }

    const patterns = data.patterns || [];
    renderPatternList(patterns);

    // Update badge
    if (patterns.length > 0) {
      badge.textContent = patterns.length;
      badge.classList.remove("hidden");
    } else {
      badge.classList.add("hidden");
    }
  } catch (e) {
    console.error("Error fetching patterns:", e);
    const errorTemplate = /** @type {HTMLTemplateElement} */ (
      document.getElementById("text-error-template")
    );
    const errorEl = /** @type {HTMLElement} */ (
      errorTemplate.content.cloneNode(true)
    ).firstElementChild;
    errorEl.textContent = "Lỗi kết nối";
    listContainer.innerHTML = "";
    listContainer.appendChild(errorEl);
  }
}

function renderPatternList(patterns) {
  const listContainer = document.getElementById("pattern-list-container");
  listContainer.innerHTML = "";

  if (patterns.length === 0) {
    const infoTemplate = /** @type {HTMLTemplateElement} */ (
      document.getElementById("text-info-template")
    );
    const infoEl = /** @type {HTMLElement} */ (
      infoTemplate.content.cloneNode(true)
    ).firstElementChild;
    infoEl.textContent = "Không tìm thấy mô hình nào";
    listContainer.appendChild(infoEl);
    return;
  }

  const patternTemplate = /** @type {HTMLTemplateElement} */ (
    document.getElementById("pattern-item-template")
  );

  patterns.forEach((p) => {
    const item = /** @type {HTMLElement} */ (
      /** @type {DocumentFragment} */ (patternTemplate.content.cloneNode(true))
        .firstElementChild
    );

    const isBullish = p.signal === "bullish";

    // Set pattern name
    const nameEl = item.querySelector(".pattern-name");
    nameEl.textContent = p.name;

    // Set signal with appropriate styling
    const signalEl = item.querySelector(".pattern-signal");
    signalEl.textContent = p.signal;
    signalEl.classList.add(
      ...(isBullish
        ? [
            "bg-green-100",
            "text-green-700",
            "dark:bg-green-900/30",
            "dark:text-green-400",
          ]
        : [
            "bg-red-100",
            "text-red-700",
            "dark:bg-red-900/30",
            "dark:text-red-400",
          ]),
    );

    // Set date
    const dateEl = item.querySelector(".pattern-date");
    dateEl.textContent = p.date;

    // Set price with color
    const priceEl = item.querySelector(".pattern-price");
    priceEl.textContent = formatPrice(p.price);
    priceEl.classList.add(isBullish ? "text-green-500" : "text-red-500");

    item.onclick = () => {
      togglePatternOnChart(p, item);
      // Close dropdown on selection
      const panel = document.getElementById("pattern-dropdown-panel");
      const chevron = document.getElementById("pattern-chevron");
      if (panel) panel.classList.add("hidden");
      if (chevron) chevron.style.transform = "rotate(0deg)";
    };
    listContainer.appendChild(item);

    // Check if this pattern is already displayed and show check icon
    const patternKey = `${p.date}_${p.name}`;
    if (displayedPatternMarkers.has(patternKey)) {
      const checkIcon = item.querySelector(".pattern-check");
      if (checkIcon) {
        checkIcon.classList.remove("hidden");
      }
    }

    // Initialize lucide icons for this item
    lucide.createIcons({ root: item });
  });
}

/**
 * Toggle pattern display on chart - adds if not shown, removes if already shown
 * @param {object} pattern - Pattern data from API
 * @param {HTMLElement} itemEl - The pattern list item element
 */
function togglePatternOnChart(pattern, itemEl) {
  if (!candleSeries) return;

  const patternKey = `${pattern.date}_${pattern.name}`;
  const checkIcon = itemEl.querySelector(".pattern-check");

  // Check if pattern is already displayed
  if (displayedPatternMarkers.has(patternKey)) {
    // Remove pattern from map
    displayedPatternMarkers.delete(patternKey);

    // Hide check icon
    if (checkIcon) {
      checkIcon.classList.add("hidden");
    }
  } else {
    // Add pattern to map
    const patternTime = new Date(pattern.date).getTime() / 1000;
    const isBullish = pattern.signal === "bullish";
    const marker = {
      time: patternTime,
      position: isBullish ? "belowBar" : "aboveBar",
      color: isBullish ? "#22c55e" : "#ef4444",
      shape: isBullish ? "arrowUp" : "arrowDown",
      text: pattern.name,
      size: 1,
    };

    displayedPatternMarkers.set(patternKey, marker);

    // Show check icon
    if (checkIcon) {
      checkIcon.classList.remove("hidden");
    }
  }

  // Update chart markers with all currently displayed patterns
  const allMarkers = Array.from(displayedPatternMarkers.values()).sort(
    (a, b) => a.time - b.time,
  );

  // Create or update markers primitive
  if (markersPrimitive) {
    markersPrimitive.setMarkers(allMarkers);
  } else if (allMarkers.length > 0) {
    markersPrimitive = LightweightCharts.createSeriesMarkers(
      candleSeries,
      allMarkers,
    );
  }
}

// =============================================================================
// CHART PATTERNS (Double Top, Head & Shoulders, Triangles, Wedges, etc.)
// =============================================================================

/** @type {Map<string, {series: object[], priceLines: object[]}>} Store chart pattern line series and price lines by pattern key */
let displayedChartPatterns = new Map();
/** @type {object[]} Store S/R zone price lines */
let displayedSRZones = [];

// Flags for dropdown initialization
let chartPatternDropdownInitialized = false;
let srZoneDropdownInitialized = false;

/**
 * Initialize chart pattern dropdown (Double Top, H&S, Triangles, etc.)
 */
function initChartPatternDropdown() {
  if (chartPatternDropdownInitialized) return;

  const trigger = document.getElementById("chart-pattern-dropdown-trigger");
  const panel = document.getElementById("chart-pattern-dropdown-panel");
  const container = document.getElementById("chart-pattern-dropdown-container");
  const chevron = /** @type {HTMLElement|null} */ (
    trigger?.querySelector('[data-lucide="chevron-down"]')
  );

  if (!trigger || !panel) return;

  chartPatternDropdownInitialized = true;

  trigger.addEventListener("click", (e) => {
    e.stopPropagation();
    const isHidden = panel.classList.toggle("hidden");
    if (!isHidden) {
      // Close others if we are opening
      closeAllDropdowns("chart-pattern-dropdown-panel");

      if (chevron) chevron.style.transform = "rotate(180deg)";
      updateDropdownPosition(trigger, panel);

      // Auto scan if empty or first open
      const listContainer = document.getElementById(
        "chart-pattern-list-container",
      );
      if (
        listContainer &&
        listContainer.children.length <= 1 &&
        currentChartSymbol
      ) {
        fetchChartPatterns(currentChartSymbol);
      }
    } else {
      if (chevron) chevron.style.transform = "rotate(0deg)";
    }
  });

  // Close when clicking outside
  document.addEventListener("click", (e) => {
    if (
      e.target instanceof Node &&
      container &&
      !container.contains(e.target)
    ) {
      panel.classList.add("hidden");
      if (chevron) chevron.style.transform = "rotate(0deg)";
    }
  });

  // Prevent closing when clicking inside panel
  panel.addEventListener("click", (e) => {
    e.stopPropagation();
  });
}

/**
 * Fetch chart patterns from API
 * @param {string} symbol - Stock ticker
 */
async function fetchChartPatterns(symbol) {
  const listContainer = document.getElementById("chart-pattern-list-container");
  const badge = document.getElementById("chart-pattern-count-badge");

  if (!listContainer) return;

  const spinnerTemplate = /** @type {HTMLTemplateElement} */ (
    document.getElementById("loading-spinner-template")
  );
  listContainer.innerHTML = "";
  listContainer.appendChild(spinnerTemplate.content.cloneNode(true));

  try {
    const intervalEl = /** @type {HTMLSelectElement} */ (
      document.getElementById("chart-interval")
    );
    const interval = intervalEl ? intervalEl.value : "1D";
    const response = await fetch(
      `/chart-patterns/${symbol}?start=${currentChartStart}&end=${currentChartEnd}&interval=${interval}`,
    );

    const data = await response.json();

    if (data.error) {
      const errorTemplate = /** @type {HTMLTemplateElement} */ (
        document.getElementById("text-error-template")
      );
      const errorEl = /** @type {HTMLElement} */ (
        errorTemplate.content.cloneNode(true)
      ).firstElementChild;
      errorEl.textContent = data.error;
      listContainer.innerHTML = "";
      listContainer.appendChild(errorEl);
      return;
    }

    const patterns = data.patterns || [];
    renderChartPatternList(patterns);

    // Update badge
    if (badge) {
      if (patterns.length > 0) {
        badge.textContent = patterns.length;
        badge.classList.remove("hidden");
      } else {
        badge.classList.add("hidden");
      }
    }
  } catch (e) {
    console.error("Error fetching chart patterns:", e);
    const errorTemplate = /** @type {HTMLTemplateElement} */ (
      document.getElementById("text-error-template")
    );
    const errorEl = /** @type {HTMLElement} */ (
      errorTemplate.content.cloneNode(true)
    ).firstElementChild;
    errorEl.textContent = "Lỗi kết nối";
    listContainer.innerHTML = "";
    listContainer.appendChild(errorEl);
  }
}

/**
 * Render chart pattern list
 * @param {object[]} patterns - List of chart patterns
 */
function renderChartPatternList(patterns) {
  const listContainer = document.getElementById("chart-pattern-list-container");
  if (!listContainer) return;

  listContainer.innerHTML = "";

  if (patterns.length === 0) {
    const infoTemplate = /** @type {HTMLTemplateElement} */ (
      document.getElementById("text-info-template")
    );
    const infoEl = /** @type {HTMLElement} */ (
      infoTemplate.content.cloneNode(true)
    ).firstElementChild;
    infoEl.textContent = "Không tìm thấy mô hình giá nào";
    listContainer.appendChild(infoEl);
    return;
  }

  // Group patterns by type for better display
  const patternNames = {
    double_top: "Double Top",
    double_bottom: "Double Bottom",
    head_and_shoulders: "Head & Shoulders",
    inverse_head_and_shoulders: "Inv. Head & Shoulders",
    ascending_triangle: "Ascending Triangle",
    descending_triangle: "Descending Triangle",
    symmetrical_triangle: "Symmetrical Triangle",
    rising_wedge: "Rising Wedge",
    falling_wedge: "Falling Wedge",
    rectangle: "Rectangle",
  };

  const patternTemplate = /** @type {HTMLTemplateElement} */ (
    document.getElementById("chart-pattern-item-template")
  );

  patterns.forEach((p) => {
    const item = /** @type {HTMLElement} */ (
      /** @type {DocumentFragment} */ (patternTemplate.content.cloneNode(true))
        .firstElementChild
    );

    const isBullish = p.signal === "bullish";
    const signalColor = isBullish
      ? "text-green-500"
      : p.signal === "bearish"
        ? "text-red-500"
        : "text-yellow-500";
    const signalBg = isBullish
      ? "bg-green-100 dark:bg-green-900/30"
      : p.signal === "bearish"
        ? "bg-red-100 dark:bg-red-900/30"
        : "bg-yellow-100 dark:bg-yellow-900/30";

    // Set pattern name
    item.querySelector(".chart-pattern-name").textContent =
      patternNames[p.type] || p.type;

    // Set signal
    const signalEl = item.querySelector(".chart-pattern-signal");
    signalEl.textContent = p.signal;
    signalEl.className = `chart-pattern-signal text-xs px-1.5 py-0.5 rounded ${signalBg} ${signalColor}`;

    // Set confidence
    item.querySelector(".chart-pattern-confidence").textContent = p.confidence
      ? Math.round(p.confidence * 100) + "%"
      : "";

    // Set date range
    item.querySelector(".chart-pattern-date-range").textContent =
      `${p.start_date} → ${p.end_date}`;

    // Set target
    const targetEl = item.querySelector(".chart-pattern-target");
    targetEl.textContent = `Target: ${formatPrice(p.target)}`;
    targetEl.className = `chart-pattern-target whitespace-nowrap ${signalColor}`;

    item.onclick = () => {
      toggleChartPatternOnChart(p, item);
      // Close dropdown on selection
      const panel = document.getElementById("chart-pattern-dropdown-panel");
      const trigger = document.getElementById("chart-pattern-dropdown-trigger");
      const chevron = /** @type {HTMLElement|null} */ (
        trigger?.querySelector('[data-lucide="chevron-down"]')
      );
      if (panel) panel.classList.add("hidden");
      if (chevron) chevron.style.transform = "rotate(0deg)";
    };
    listContainer.appendChild(item);

    // Check if already displayed
    const patternKey = `${p.type}_${p.start_date}`;
    if (displayedChartPatterns.has(patternKey)) {
      const checkIcon = item.querySelector(".pattern-check");
      if (checkIcon) checkIcon.classList.remove("hidden");
      item.classList.add("border-blue-500", "dark:border-blue-400");
    }

    lucide.createIcons({ root: item });
  });
}

/**
 * Toggle chart pattern visualization on chart
 * @param {object} pattern - Chart pattern data
 * @param {HTMLElement} itemEl - List item element
 */
function toggleChartPatternOnChart(pattern, itemEl) {
  if (!candleSeries || !priceChart) return;

  const patternKey = `${pattern.type}_${pattern.start_date}`;
  const checkIcon = itemEl.querySelector(".pattern-check");

  if (displayedChartPatterns.has(patternKey)) {
    // Remove pattern lines and price lines
    const patternData = displayedChartPatterns.get(patternKey);

    // Remove line series
    patternData.series.forEach((line) => {
      try {
        priceChart.removeSeries(line);
      } catch (e) {
        console.warn("Error removing pattern line:", e);
      }
    });

    // Remove price lines (neckline, target)
    patternData.priceLines.forEach((priceLine) => {
      try {
        candleSeries.removePriceLine(priceLine);
      } catch (e) {
        console.warn("Error removing price line:", e);
      }
    });

    displayedChartPatterns.delete(patternKey);

    if (checkIcon) checkIcon.classList.add("hidden");
    itemEl.classList.remove("border-blue-500", "dark:border-blue-400");
  } else {
    // Add pattern visualization based on type
    const lines = [];
    const priceLines = [];
    const isBullish = pattern.signal === "bullish";
    const lineColor = isBullish
      ? "#22c55e"
      : pattern.signal === "bearish"
        ? "#ef4444"
        : "#eab308";

    // Draw trendlines for patterns that have them
    if (pattern.trendlines) {
      // Resistance trendline
      if (
        pattern.trendlines.resistance &&
        pattern.trendlines.resistance.length >= 2
      ) {
        const resistanceData = pattern.trendlines.resistance.map((pt) => ({
          time: new Date(pt.date).getTime() / 1000,
          value: pt.price,
        }));
        const resistanceLine = priceChart.addSeries(
          LightweightCharts.LineSeries,
          {
            color: "#ef4444",
            lineWidth: 2,
            lineStyle: LightweightCharts.LineStyle.Dashed,
            priceLineVisible: false,
            lastValueVisible: false,
          },
          0,
        );
        resistanceLine.setData(resistanceData);
        lines.push(resistanceLine);
      }

      // Support trendline
      if (
        pattern.trendlines.support &&
        pattern.trendlines.support.length >= 2
      ) {
        const supportData = pattern.trendlines.support.map((pt) => ({
          time: new Date(pt.date).getTime() / 1000,
          value: pt.price,
        }));
        const supportLine = priceChart.addSeries(
          LightweightCharts.LineSeries,
          {
            color: "#22c55e",
            lineWidth: 2,
            lineStyle: LightweightCharts.LineStyle.Dashed,
            priceLineVisible: false,
            lastValueVisible: false,
          },
          0,
        );
        supportLine.setData(supportData);
        lines.push(supportLine);
      }
    }

    // Draw key points for patterns like Double Top, H&S
    if (pattern.key_points && pattern.key_points.length > 0) {
      const keyPointsData = pattern.key_points.map((pt) => ({
        time: new Date(pt.date).getTime() / 1000,
        value: pt.price,
      }));
      const keyPointsLine = priceChart.addSeries(
        LightweightCharts.LineSeries,
        {
          color: lineColor,
          lineWidth: 2,
          priceLineVisible: false,
          lastValueVisible: false,
        },
        0,
      );
      keyPointsLine.setData(keyPointsData);
      lines.push(keyPointsLine);
    }

    // Draw neckline for patterns that have one
    if (pattern.neckline) {
      const necklinePriceLine = candleSeries.createPriceLine({
        price: pattern.neckline,
        color: "#6366f1",
        lineWidth: 2,
        lineStyle: LightweightCharts.LineStyle.Solid,
        axisLabelVisible: true,
        title: "Neckline",
      });
      priceLines.push(necklinePriceLine);
    }

    // Draw target price line
    if (pattern.target) {
      const targetPriceLine = candleSeries.createPriceLine({
        price: pattern.target,
        color: isBullish ? "#22c55e" : "#ef4444",
        lineWidth: 1,
        lineStyle: LightweightCharts.LineStyle.Dotted,
        axisLabelVisible: true,
        title: "Target",
      });
      priceLines.push(targetPriceLine);
    }

    displayedChartPatterns.set(patternKey, { series: lines, priceLines });

    if (checkIcon) checkIcon.classList.remove("hidden");
    itemEl.classList.add("border-blue-500", "dark:border-blue-400");
  }
}

// =============================================================================
// SUPPORT/RESISTANCE ZONES
// =============================================================================

/**
 * Initialize S/R zone dropdown
 */
function initSRZoneDropdown() {
  if (srZoneDropdownInitialized) return;

  const trigger = document.getElementById("sr-zone-dropdown-trigger");
  const panel = document.getElementById("sr-zone-dropdown-panel");
  const container = document.getElementById("sr-zone-dropdown-container");
  const chevron = /** @type {HTMLElement|null} */ (
    trigger?.querySelector('[data-lucide="chevron-down"]')
  );

  if (!trigger || !panel) return;

  srZoneDropdownInitialized = true;

  trigger.addEventListener("click", (e) => {
    e.stopPropagation();
    const isHidden = panel.classList.toggle("hidden");
    if (!isHidden) {
      // Close others if we are opening
      closeAllDropdowns("sr-zone-dropdown-panel");

      if (chevron) chevron.style.transform = "rotate(180deg)";
      updateDropdownPosition(trigger, panel);

      // Auto scan if empty or first open
      const listContainer = document.getElementById("sr-zone-list-container");
      if (
        listContainer &&
        listContainer.children.length <= 1 &&
        currentChartSymbol
      ) {
        fetchSupportResistance(currentChartSymbol);
      }
    } else {
      if (chevron) chevron.style.transform = "rotate(0deg)";
    }
  });

  // Close when clicking outside
  document.addEventListener("click", (e) => {
    if (
      e.target instanceof Node &&
      container &&
      !container.contains(e.target)
    ) {
      panel.classList.add("hidden");
      if (chevron) chevron.style.transform = "rotate(0deg)";
    }
  });

  // Prevent closing when clicking inside panel
  panel.addEventListener("click", (e) => {
    e.stopPropagation();
  });
}

/**
 * Fetch support/resistance zones from API
 * @param {string} symbol - Stock ticker
 */
async function fetchSupportResistance(symbol) {
  const listContainer = document.getElementById("sr-zone-list-container");
  if (!listContainer) return;

  const spinnerTemplate = /** @type {HTMLTemplateElement} */ (
    document.getElementById("loading-spinner-template")
  );
  listContainer.innerHTML = "";
  listContainer.appendChild(spinnerTemplate.content.cloneNode(true));

  try {
    const intervalEl = /** @type {HTMLSelectElement} */ (
      document.getElementById("chart-interval")
    );
    const interval = intervalEl ? intervalEl.value : "1D";
    const response = await fetch(
      `/support-resistance/${symbol}?start=${currentChartStart}&end=${currentChartEnd}&interval=${interval}`,
    );

    const data = await response.json();

    if (data.error) {
      const errorTemplate = /** @type {HTMLTemplateElement} */ (
        document.getElementById("text-error-template")
      );
      const errorEl = /** @type {HTMLElement} */ (
        errorTemplate.content.cloneNode(true)
      ).firstElementChild;
      errorEl.textContent = data.error;
      listContainer.innerHTML = "";
      listContainer.appendChild(errorEl);
      return;
    }

    renderSRZoneList(data);
  } catch (e) {
    console.error("Error fetching S/R zones:", e);
    const errorTemplate = /** @type {HTMLTemplateElement} */ (
      document.getElementById("text-error-template")
    );
    const errorEl = /** @type {HTMLElement} */ (
      errorTemplate.content.cloneNode(true)
    ).firstElementChild;
    errorEl.textContent = "Lỗi kết nối";
    listContainer.innerHTML = "";
    listContainer.appendChild(errorEl);
  }
}

/**
 * Render S/R zone list
 * @param {object} data - S/R zone data from API
 */
function renderSRZoneList(data) {
  const listContainer = document.getElementById("sr-zone-list-container");
  if (!listContainer) return;

  listContainer.innerHTML = "";

  const supportZones = data.support_zones || [];
  const resistanceZones = data.resistance_zones || [];
  const currentPrice = data.current_price;

  if (supportZones.length === 0 && resistanceZones.length === 0) {
    const infoTemplate = /** @type {HTMLTemplateElement} */ (
      document.getElementById("text-info-template")
    );
    const infoEl = /** @type {HTMLElement} */ (
      infoTemplate.content.cloneNode(true)
    ).firstElementChild;
    infoEl.textContent = "Không tìm thấy vùng S/R nào";
    listContainer.appendChild(infoEl);
    return;
  }

  // Header for resistance zones
  if (resistanceZones.length > 0) {
    const header = document.createElement("div");
    header.className =
      "text-xs font-semibold text-red-500 dark:text-red-400 mb-1 px-2";
    header.textContent = `Kháng cự (${resistanceZones.length})`;
    listContainer.appendChild(header);

    resistanceZones.forEach((zone) => {
      const item = createSRZoneItem(zone, "resistance", currentPrice);
      listContainer.appendChild(item);
    });
  }

  // Header for support zones
  if (supportZones.length > 0) {
    const header = document.createElement("div");
    header.className =
      "text-xs font-semibold text-green-500 dark:text-green-400 mb-1 mt-2 px-2";
    header.textContent = `Hỗ trợ (${supportZones.length})`;
    listContainer.appendChild(header);

    supportZones.forEach((zone) => {
      const item = createSRZoneItem(zone, "support", currentPrice);
      listContainer.appendChild(item);
    });
  }
}

/**
 * Create S/R zone list item
 * @param {object} zone - Zone data
 * @param {string} type - "support" or "resistance"
 * @param {number} currentPrice - Current stock price
 */
function createSRZoneItem(zone, type, currentPrice) {
  const isSupport = type === "support";
  const distancePercent = ((currentPrice - zone.price) / zone.price) * 100;
  const distanceLabel =
    distancePercent > 0
      ? `+${distancePercent.toFixed(1)}%`
      : `${distancePercent.toFixed(1)}%`;
  const template = /** @type {HTMLTemplateElement} */ (
    document.getElementById("sr-zone-item-template")
  );
  const item = /** @type {HTMLElement} */ (
    /** @type {DocumentFragment} */ (template.content.cloneNode(true))
      .firstElementChild
  );

  // Set price and color
  const priceEl = item.querySelector(".sr-zone-price");
  priceEl.textContent = formatPrice(zone.price);
  priceEl.classList.add(
    isSupport ? "text-green-600" : "text-red-600",
    isSupport ? "dark:text-green-400" : "dark:text-red-400",
  );

  // Set strength
  item.querySelector(".sr-zone-strength").textContent = `x${zone.strength}`;

  // Set distance
  item.querySelector(".sr-zone-distance").textContent = distanceLabel;

  // Set range
  item.querySelector(".sr-zone-range").textContent = `Range: ${formatPrice(
    zone.range[0],
  )} - ${formatPrice(zone.range[1])}`;

  const zoneKey = `${type}_${zone.price}`;
  item.onclick = () => {
    toggleSRZoneOnChart(zone, type, item, zoneKey);
    // Close dropdown on selection
    const panel = document.getElementById("sr-zone-dropdown-panel");
    const trigger = document.getElementById("sr-zone-dropdown-trigger");
    const chevron = /** @type {HTMLElement|null} */ (
      trigger?.querySelector('[data-lucide="chevron-down"]')
    );
    if (panel) panel.classList.add("hidden");
    if (chevron) chevron.style.transform = "rotate(0deg)";
  };

  // Check if already displayed
  if (displayedSRZones.some((z) => z.key === zoneKey)) {
    const checkIcon = item.querySelector(".sr-check");
    if (checkIcon) checkIcon.classList.remove("hidden");
    item.classList.add("border-blue-500", "dark:border-blue-400", "selected");
  } else {
    // Ensure we clean up if not selected (though unlikely on create)
    item.classList.remove("selected");
  }

  lucide.createIcons({ root: item });
  return item;
}

/**
 * Toggle S/R zone on chart as a band/area
 * @param {object} zone - Zone data
 * @param {string} type - "support" or "resistance"
 * @param {HTMLElement} itemEl - List item element
 * @param {string} zoneKey - Unique key for the zone
 */
function toggleSRZoneOnChart(zone, type, itemEl, zoneKey) {
  if (!candleSeries) return;

  const checkIcon = itemEl.querySelector(".sr-check");
  const existingIndex = displayedSRZones.findIndex((z) => z.key === zoneKey);

  if (existingIndex >= 0) {
    // Remove zone - clear price lines and series
    const existing = displayedSRZones[existingIndex];
    if (existing.lines) {
      existing.lines.forEach((line) => {
        try {
          // Try removePriceLine first (for center price line)
          candleSeries.removePriceLine(line);
        } catch (e) {
          try {
            // Fall back to removeSeries (for area series rectangles)
            priceChart.removeSeries(line);
          } catch (e2) {
            console.warn("Error removing zone element:", e2);
          }
        }
      });
    }
    displayedSRZones.splice(existingIndex, 1);

    if (checkIcon) checkIcon.classList.add("hidden");
    itemEl.classList.remove(
      "border-blue-500",
      "dark:border-blue-400",
      "selected",
    );
  } else {
    // Add zone as a band with upper and lower lines
    const isSupport = type === "support";
    const color = isSupport ? "#22c55e" : "#ef4444";
    const lines = [];

    // Create center line
    const centerLine = candleSeries.createPriceLine({
      price: zone.price,
      color: color,
      lineWidth: 2,
      lineStyle: LightweightCharts.LineStyle.Solid,
      axisLabelVisible: true,
      title: isSupport ? "S" : "R",
    });
    lines.push(centerLine);

    // Create filled rectangle for the zone range if different from center
    if (zone.range[0] !== zone.price || zone.range[1] !== zone.price) {
      // Get time range from candle data
      const candleData = candleSeries.data();
      if (candleData && candleData.length > 0) {
        const startTime = candleData[0].time;
        const endTime = candleData[candleData.length - 1].time;

        // Use BaselineSeries to fill only between upper and lower bounds
        const zoneArea = priceChart.addSeries(
          LightweightCharts.BaselineSeries,
          {
            baseValue: { type: "price", price: zone.range[0] }, // Lower bound
            topLineColor: color + "60", // Upper line color
            topFillColor1: color + "30", // Fill between upper and base
            topFillColor2: color + "30",
            bottomLineColor: "transparent", // No line below base
            bottomFillColor1: "transparent", // No fill below base
            bottomFillColor2: "transparent",
            lineWidth: 1,
            priceLineVisible: false,
            lastValueVisible: false,
            crosshairMarkerVisible: false,
          },
          0,
        );

        // Set data at the upper bound
        const zoneData = [
          { time: startTime, value: zone.range[1] },
          { time: endTime, value: zone.range[1] },
        ];
        zoneArea.setData(zoneData);

        lines.push(zoneArea);
      }
    }

    displayedSRZones.push({ key: zoneKey, lines: lines });

    if (checkIcon) checkIcon.classList.remove("hidden");
    itemEl.classList.add("border-blue-500", "dark:border-blue-400", "selected");
  }
}

/**
 * Clear all displayed chart patterns and S/R zones
 */
function clearAllPatternVisualizations() {
  // Clear chart patterns
  displayedChartPatterns.forEach((patternData) => {
    patternData.series.forEach((line) => {
      try {
        priceChart.removeSeries(line);
      } catch (e) {}
    });
    patternData.priceLines.forEach((priceLine) => {
      try {
        candleSeries.removePriceLine(priceLine);
      } catch (e) {}
    });
  });
  displayedChartPatterns.clear();

  // Clear S/R zones (mix of price lines and area series)
  displayedSRZones.forEach((zone) => {
    if (zone.lines) {
      zone.lines.forEach((line) => {
        try {
          candleSeries.removePriceLine(line);
        } catch (e) {
          try {
            priceChart.removeSeries(line);
          } catch (e2) {}
        }
      });
    }
  });
  displayedSRZones.length = 0;

  // Clear candlestick pattern markers
  displayedPatternMarkers.clear();
  if (markersPrimitive) {
    markersPrimitive.setMarkers([]);
  }
}

/**
 * Clear all pattern list UIs and badges
 */
function clearPatternListUI() {
  // Clear candlestick pattern list
  const patternListContainer = document.getElementById(
    "pattern-list-container",
  );
  if (patternListContainer) {
    patternListContainer.innerHTML = `<div class="flex items-center justify-center h-20 text-xs text-slate-400 italic">Nhấn "Quét" để tìm mô hình</div>`;
  }
  const patternBadge = document.getElementById("pattern-count-badge");
  if (patternBadge) {
    patternBadge.classList.add("hidden");
  }

  // Clear chart pattern list
  const chartPatternListContainer = document.getElementById(
    "chart-pattern-list-container",
  );
  if (chartPatternListContainer) {
    chartPatternListContainer.innerHTML = `<div class="flex items-center justify-center h-20 text-xs text-slate-400 italic">Nhấn "Quét" để tìm mô hình</div>`;
  }
  const chartPatternBadge = document.getElementById(
    "chart-pattern-count-badge",
  );
  if (chartPatternBadge) {
    chartPatternBadge.classList.add("hidden");
  }

  // Clear S/R zone list
  const srZoneListContainer = document.getElementById("sr-zone-list-container");
  if (srZoneListContainer) {
    srZoneListContainer.innerHTML = `<div class="flex items-center justify-center h-20 text-xs text-slate-400 italic">Nhấn "Quét" để tìm vùng S/R</div>`;
  }
  const srZoneBadge = document.getElementById("sr-zone-count-badge");
  if (srZoneBadge) {
    srZoneBadge.classList.add("hidden");
  }

  // Clear analysis method list
  const analysisMethodListContainer = document.getElementById(
    "analysis-method-list-container",
  );
  if (analysisMethodListContainer) {
    analysisMethodListContainer.innerHTML = `<div class="flex items-center justify-center h-20 text-xs text-slate-400 italic">Đang tải...</div>`;
  }
  const analysisMethodBadge = document.getElementById(
    "analysis-method-name-badge",
  );
  if (analysisMethodBadge) {
    analysisMethodBadge.classList.add("hidden");
    analysisMethodBadge.textContent = "";
  }
  const analysisMethodActiveLabel = document.getElementById(
    "analysis-method-active",
  );
  if (analysisMethodActiveLabel) {
    analysisMethodActiveLabel.classList.add("hidden");
    analysisMethodActiveLabel.textContent = "";
  }
  currentAnalysisMethod = null;
}

// =============================================================================
// TECHNICAL ANALYSIS METHODS DROPDOWN
// =============================================================================

/**
 * Initialize analysis method dropdown
 */
function initAnalysisMethodDropdown() {
  if (analysisMethodDropdownInitialized) return;

  const trigger = document.getElementById("analysis-method-dropdown-trigger");
  const panel = document.getElementById("analysis-method-dropdown-panel");
  const container = document.getElementById(
    "analysis-method-dropdown-container",
  );

  if (!trigger || !panel) return;

  analysisMethodDropdownInitialized = true;

  trigger.addEventListener("click", (e) => {
    e.stopPropagation();

    // Re-query chevron to handle Lucide replacement
    const chevron = /** @type {HTMLElement|null} */ (
      trigger?.querySelector('[data-lucide="chevron-down"]')
    );

    const isHidden = panel.classList.toggle("hidden");
    if (!isHidden) {
      // Close others if we are opening
      closeAllDropdowns("analysis-method-dropdown-panel");

      if (chevron) chevron.style.transform = "rotate(180deg)";
      updateDropdownPosition(trigger, panel);

      // Fetch methods on first open
      const listContainer = document.getElementById(
        "analysis-method-list-container",
      );
      if (
        listContainer &&
        listContainer.children.length <= 1 &&
        currentChartSymbol
      ) {
        fetchAnalysisMethods(currentChartSymbol);
      }
    } else {
      if (chevron) chevron.style.transform = "rotate(0deg)";
    }
  });

  // Close when clicking outside
  document.addEventListener("click", (e) => {
    if (
      e.target instanceof Node &&
      container &&
      !container.contains(e.target)
    ) {
      panel.classList.add("hidden");

      const chevron = /** @type {HTMLElement|null} */ (
        trigger?.querySelector('[data-lucide="chevron-down"]')
      );
      if (chevron) chevron.style.transform = "rotate(0deg)";
    }
  });

  // Prevent closing when clicking inside panel
  panel.addEventListener("click", (e) => {
    e.stopPropagation();
  });
}

/**
 * Fetch analysis methods from API
 * @param {string} symbol - Stock ticker
 */
async function fetchAnalysisMethods(symbol) {
  const listContainer = document.getElementById(
    "analysis-method-list-container",
  );
  if (!listContainer) return;

  // Show loading
  listContainer.innerHTML = `<div class="flex items-center justify-center h-20 text-xs text-slate-400 italic">Đang tải...</div>`;

  try {
    const response = await fetch(
      `/analysis-methods/${symbol}?start=${currentChartStart}&end=${currentChartEnd}&interval=${currentInterval}`,
    );

    const data = await response.json();

    if (data.error) {
      listContainer.innerHTML = `<div class="flex items-center justify-center h-20 text-xs text-red-400">${data.error}</div>`;
      return;
    }

    renderAnalysisMethodList(data.methods || []);
  } catch (err) {
    console.error("Error fetching analysis methods:", err);
    listContainer.innerHTML = `<div class="flex items-center justify-center h-20 text-xs text-red-400">Lỗi tải dữ liệu</div>`;
  }
}

/**
 * Render analysis method list
 * @param {Array} methods - Array of method objects
 */
function renderAnalysisMethodList(methods) {
  const listContainer = document.getElementById(
    "analysis-method-list-container",
  );
  if (!listContainer) return;

  if (!methods || methods.length === 0) {
    listContainer.innerHTML = `<div class="flex items-center justify-center h-20 text-xs text-slate-400 italic">Không có dữ liệu</div>`;
    return;
  }

  const template = /** @type {HTMLTemplateElement} */ (
    document.getElementById("analysis-method-item-template")
  );
  if (!template) return;

  listContainer.innerHTML = "";

  methods.forEach((method) => {
    const clone = /** @type {HTMLElement} */ (template.content.cloneNode(true));
    const item = /** @type {HTMLElement} */ (
      clone.querySelector(".analysis-method-item")
    );
    if (!item) return;

    // Set data attribute
    item.dataset.methodId = method.id;

    // Name
    const nameEl = item.querySelector(".method-name");
    if (nameEl) nameEl.textContent = method.name || "";

    // Category
    const categoryEl = item.querySelector(".method-category");
    if (categoryEl) categoryEl.textContent = method.category || "";

    // Signal badge
    const signalEl = /** @type {HTMLElement} */ (
      item.querySelector(".method-signal")
    );
    if (signalEl) {
      const signal = method.signal || "Neutral";
      signalEl.textContent = signal;

      // Apply signal colors
      if (signal === "Bullish") {
        signalEl.classList.add(
          "bg-green-100",
          "text-green-700",
          "dark:bg-green-900/30",
          "dark:text-green-400",
        );
      } else if (signal === "Bearish") {
        signalEl.classList.add(
          "bg-red-100",
          "text-red-700",
          "dark:bg-red-900/30",
          "dark:text-red-400",
        );
      } else {
        signalEl.classList.add(
          "bg-gray-100",
          "text-gray-600",
          "dark:bg-gray-700",
          "dark:text-gray-400",
        );
      }
    }

    // Confidence
    const confidenceEl = item.querySelector(".method-confidence");
    if (confidenceEl) {
      const confidence = method.confidence || "";
      confidenceEl.textContent = confidence;
    }

    // Description
    const descriptionEl = item.querySelector(".method-description");
    if (descriptionEl) descriptionEl.textContent = method.description || "";

    // Evaluation (hidden by default, shown when selected)
    const evaluationEl = item.querySelector(".method-evaluation");
    if (evaluationEl) evaluationEl.textContent = method.evaluation || "";

    // Mark as selected if this is the current method
    if (currentAnalysisMethod === method.id) {
      item.classList.add(
        "bg-primary-50",
        "dark:bg-primary-900/20",
        "border-primary-200",
        "dark:border-primary-700",
      );
      const checkIcon = item.querySelector(".method-check");
      if (checkIcon) checkIcon.classList.remove("hidden");
      if (evaluationEl) evaluationEl.classList.remove("hidden");
    }

    // Click handler
    item.addEventListener("click", () => {
      toggleAnalysisMethod(method);
    });

    listContainer.appendChild(clone);
  });

  // Re-initialize Lucide icons
  if (typeof lucide !== "undefined") {
    lucide.createIcons();
  }
}

/**
 * Toggle analysis method selection (single-select)
 * @param {Object} method - Method object
 */
function toggleAnalysisMethod(method) {
  const items = document.querySelectorAll(".analysis-method-item");
  const activeLabel = document.getElementById("analysis-method-active");
  const badge = document.getElementById("analysis-method-name-badge");

  if (currentAnalysisMethod === method.id) {
    // Deselect
    currentAnalysisMethod = null;
    clearAnalysisMethodVisualization();

    items.forEach((item) => {
      item.classList.remove(
        "bg-primary-50",
        "dark:bg-primary-900/20",
        "border-primary-200",
        "dark:border-primary-700",
      );
      const checkIcon = item.querySelector(".method-check");
      if (checkIcon) checkIcon.classList.add("hidden");
      const evaluationEl = item.querySelector(".method-evaluation");
      if (evaluationEl) evaluationEl.classList.add("hidden");
    });

    if (activeLabel) {
      activeLabel.classList.add("hidden");
      activeLabel.textContent = "";
    }
    if (badge) {
      badge.classList.add("hidden");
    }
  } else {
    // Select new method (single-select)
    currentAnalysisMethod = method.id;

    // Clear previous visualizations
    clearAnalysisMethodVisualization();

    // Update UI
    items.forEach((item) => {
      const itemId = /** @type {HTMLElement} */ (item).dataset.methodId;
      if (itemId === method.id) {
        item.classList.add(
          "bg-primary-50",
          "dark:bg-primary-900/20",
          "border-primary-200",
          "dark:border-primary-700",
        );
        const checkIcon = item.querySelector(".method-check");
        if (checkIcon) checkIcon.classList.remove("hidden");
        const evaluationEl = item.querySelector(".method-evaluation");
        if (evaluationEl) evaluationEl.classList.remove("hidden");
      } else {
        item.classList.remove(
          "bg-primary-50",
          "dark:bg-primary-900/20",
          "border-primary-200",
          "dark:border-primary-700",
        );
        const checkIcon = item.querySelector(".method-check");
        if (checkIcon) checkIcon.classList.add("hidden");
        const evaluationEl = item.querySelector(".method-evaluation");
        if (evaluationEl) evaluationEl.classList.add("hidden");
      }
    });

    if (activeLabel) {
      activeLabel.textContent = method.name;
      activeLabel.classList.remove("hidden");
    }
    if (badge) {
      badge.textContent = method.name;
      badge.classList.remove("hidden");
    }

    // Draw visualization
    drawAnalysisMethodVisualization(method);
  }
}

/**
 * Clear analysis method visualization from chart
 */
function clearAnalysisMethodVisualization() {
  // Remove any series or primitives we added
  if (analysisMethodMarkers && analysisMethodMarkers.length > 0) {
    analysisMethodMarkers.forEach((item) => {
      if (!item) return;

      // Check if this is a chart markers tracker
      if (item.type === "chartMarkers") {
        // Clear markers using the stored primitive
        if (item.primitive) {
          item.primitive.setMarkers([]);
        }
        return;
      }

      const seriesObj = item.series || item; // Standardize (could be wrapped or raw priceLine)

      // Distinguish between Series (has setData) and PriceLine
      const objToRemove = seriesObj;

      if (typeof objToRemove.setData === "function") {
        // It's a Series (RSI, MACD, etc.)
        if (priceChart) {
          try {
            priceChart.removeSeries(objToRemove);
          } catch (e) {
            console.warn("Failed to remove series:", e);
          }
        }
      } else {
        // It's a PriceLine (Support/Resistance)
        if (candleSeries) {
          try {
            candleSeries.removePriceLine(objToRemove);
          } catch (e) {
            // Ignore errors for price lines
          }
        }
      }
    });
  }
  analysisMethodMarkers = [];
  activeSignalMarkers = [];

  // Clear isolated storage
  methodIndicatorValues = {};
  methodIndicatorConfigs = {};
}

/**
 * Draw visualization for selected analysis method
 * @param {Object} method - Method object with id, signal, value, etc.
 */
async function drawAnalysisMethodVisualization(method) {
  if (!priceChart || !candleSeries || !method) return;

  const symbol = currentChartSymbol;
  // Use current timeframe/interval
  const start = currentChartStart;
  const end = currentChartEnd;
  const interval = currentInterval;

  // Determine indicators to fetch based on method ID
  let indicatorsToFetch = [];

  switch (method.id) {
    case "rsi":
    case "rsi_divergence":
    case "macd_rsi_confluence":
      indicatorsToFetch.push("rsi");
      break;
    case "macd":
      indicatorsToFetch.push("macd");
      break;
    case "gold":
    case "golden_death_cross":
      indicatorsToFetch.push("ma_50", "ma_200");
      break;
    case "moving_average":
      indicatorsToFetch.push("ma_20", "ma_50", "ma_200");
      break;
    case "bollinger_bands":
    case "bb_squeeze":
      indicatorsToFetch.push("bb");
      break;
    case "stochastic":
      indicatorsToFetch.push("stoch");
      break;
    case "adx":
      indicatorsToFetch.push("adx");
      break;
    case "volume":
      indicatorsToFetch.push("obv", "cmf");
      break;
    case "volume_breakout":
      indicatorsToFetch.push("vol_sma_20");
      break;
    case "vwap":
      indicatorsToFetch.push("vwap");
      break;
    case "support_resistance":
      indicatorsToFetch.push("pivot", "fib");
      break;
  }

  // Handle combined methods
  if (method.id === "macd_rsi_confluence") {
    indicatorsToFetch.push("macd");
  }

  // Deduplicate
  indicatorsToFetch = [...new Set(indicatorsToFetch)];

  if (indicatorsToFetch.length === 0) return;

  // Fetch data
  const apiResponse = await fetchIndicatorsFromAPI(
    symbol,
    start,
    end,
    interval,
    indicatorsToFetch,
  );

  if (!apiResponse || !apiResponse.indicators) {
    console.warn("Failed to fetch visualization data");
    return;
  }

  // Pass isolated storage objects for analysis methods
  const ctx = createIndicatorContext(
    priceChart,
    candleSeries,
    methodIndicatorValues,
    methodIndicatorConfigs,
    null,
  );

  const visualizationSeries = [];

  // Render indicators
  for (const key of indicatorsToFetch) {
    const apiData = apiResponse.indicators[key];
    if (apiData && !apiData.error) {
      const results = renderIndicatorFromAPI(key, apiData, ctx);
      // results is array of {type, series}
      if (results) {
        results.forEach((item) => {
          // Attach key for cleanup
          item.key = key;
          visualizationSeries.push(item);
        });
      }
    }
  }

  // Store for cleanup
  analysisMethodMarkers = visualizationSeries;

  // Render signal markers if present in method.visualization
  if (method.visualization?.signals?.length > 0) {
    // Store original signal data for hover detection
    activeSignalMarkers = method.visualization.signals.map((sig) => ({
      time: sig.time,
      type: sig.type,
      price: sig.price,
      direction: sig.direction,
      methodName: method.name,
    }));

    const markers = activeSignalMarkers.map((sig) => ({
      time: sig.time,
      position: sig.direction === "up" ? "belowBar" : "aboveBar",
      color: sig.direction === "up" ? "#10b981" : "#ef4444",
      shape: sig.direction === "up" ? "arrowUp" : "arrowDown",
      text: sig.type,
      size: 1,
    }));

    // Sort markers by time (required by LightweightCharts)
    markers.sort((a, b) => a.time - b.time);

    // Use createSeriesMarkers API
    const markerPrimitive = LightweightCharts.createSeriesMarkers(
      candleSeries,
      markers,
    );
    // Track the primitive so we can clear it later
    analysisMethodMarkers.push({
      type: "chartMarkers",
      primitive: markerPrimitive,
    });
  }

  // Render trend lines for divergence patterns
  if (method.visualization?.signals?.length > 0) {
    method.visualization.signals.forEach((sig) => {
      // Draw price trendline on main chart
      if (sig.trendline?.price) {
        const priceTrendLine = priceChart.addSeries(
          LightweightCharts.LineSeries,
          {
            color: sig.direction === "up" ? "#10b981" : "#ef4444",
            lineWidth: 2,
            lineStyle: LightweightCharts.LineStyle.Dashed,
            crosshairMarkerVisible: false,
            priceLineVisible: false,
            lastValueVisible: false,
          },
          0,
        );
        priceTrendLine.setData(sig.trendline.price);
        analysisMethodMarkers.push({ type: "series", series: priceTrendLine });
      }

      // Draw RSI trendline on RSI indicator pane
      if (sig.trendline?.rsi) {
        // Get RSI pane from config, fallback to 2
        const rsiConfig = methodIndicatorConfigs["rsi"] || {};
        const rsiPane = rsiConfig.pane ?? 2;

        const rsiTrendLine = priceChart.addSeries(
          LightweightCharts.LineSeries,
          {
            color: sig.direction === "up" ? "#22c55e" : "#f87171",
            lineWidth: 2,
            lineStyle: LightweightCharts.LineStyle.Dashed,
            crosshairMarkerVisible: false,
            priceLineVisible: false,
            lastValueVisible: false,
          },
          rsiPane,
        );
        rsiTrendLine.setData(sig.trendline.rsi);
        analysisMethodMarkers.push({ type: "series", series: rsiTrendLine });
      }
    });
  }
}
