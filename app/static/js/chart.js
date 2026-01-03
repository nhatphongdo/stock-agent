// Chart Module - Global chart instances for cleanup (Lightweight Charts)
let priceChart = null;
let candleSeries = null;
let volumeSeries = null;
let indicatorSeries = []; // Array to hold indicator line series
let indicatorValues = {}; // Store raw indicator values mapping time -> {key: value}
let currentChartSymbol = null;
let currentChartStart = null; // Current chart start date (YYYY-MM-DD)
let currentChartEnd = null; // Current chart end date (YYYY-MM-DD)

// Indicator Configuration Registry
const INDICATOR_CONFIG = {
  // Moving Averages (overlay on price, pane 0)
  ma: { id: "indicator-ma", label: "SMA(20)", color: "#3b82f6", pane: 0 },
  ema: { id: "indicator-ema", label: "EMA(9)", color: "#f97316", pane: 0 },
  wma: { id: "indicator-wma", label: "WMA(20)", color: "#06b6d4", pane: 0 },
  vwap: { id: "indicator-vwap", label: "VWAP", color: "#8b5cf6", pane: 0 },

  // Bands/Channels (overlay on price, pane 0)
  bb: { id: "indicator-bb", label: "BB", color: "#a855f7", pane: 0 },
  atr: { id: "indicator-atr", label: "ATR(14)", color: "#ec4899", pane: 0 },

  // Oscillators (scaled to price range, pane 0)
  rsi: { id: "indicator-rsi", label: "RSI(14)", color: "#f59e0b", pane: 0 },
  macd: {
    id: "indicator-macd",
    label: "MACD",
    colors: { line: "#3b82f6", signal: "#ef4444" },
    pane: 0,
  },
  stoch: {
    id: "indicator-stoch",
    label: "Stoch",
    colors: { k: "#10b981", d: "#ef4444" },
    pane: 0,
  },
  williams: {
    id: "indicator-williams",
    label: "WillR",
    color: "#06b6d4",
    pane: 0,
  },
  cci: { id: "indicator-cci", label: "CCI(20)", color: "#8b5cf6", pane: 0 },
  roc: { id: "indicator-roc", label: "ROC(10)", color: "#f97316", pane: 0 },

  // Trend (scaled to price range, pane 0)
  adx: {
    id: "indicator-adx",
    label: "ADX(14)",
    colors: { adx: "#22c55e", plusDI: "#3b82f6", minusDI: "#ef4444" },
    pane: 0,
  },

  // Volume (in volume pane, pane 1)
  volSma: {
    id: "indicator-vol-sma",
    label: "Vol SMA(20)",
    color: "#8b5cf6",
    pane: 1,
  },
  obv: { id: "indicator-obv", label: "OBV", color: "#06b6d4", pane: 1 },
  mfi: { id: "indicator-mfi", label: "MFI(14)", color: "#f59e0b", pane: 1 },
  cmf: { id: "indicator-cmf", label: "CMF(20)", color: "#ec4899", pane: 1 },

  // Support/Resistance
  pivot: {
    id: "indicator-pivot",
    label: "Pivot S/R",
    colors: { resistance: "#ef4444", support: "#10b981", pivot: "#6366f1" },
    pane: 0,
  },
  fib: {
    id: "indicator-fib",
    label: "Fibonacci",
    colors: { level: "#f59e0b", key: "#8b5cf6" },
    pane: 0,
  },
};

// All indicator checkbox IDs
const ALL_INDICATOR_IDS = [
  "indicator-ma",
  "indicator-ema",
  "indicator-wma",
  "indicator-vwap",
  "indicator-bb",
  "indicator-atr",
  "indicator-rsi",
  "indicator-macd",
  "indicator-stoch",
  "indicator-williams",
  "indicator-cci",
  "indicator-roc",
  "indicator-adx",
  "indicator-vol-sma",
  "indicator-obv",
  "indicator-mfi",
  "indicator-cmf",
  "indicator-pivot",
  "indicator-fib",
];

// Flag to track if dropdown has been initialized after becoming visible
let indicatorDropdownInitialized = false;

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
      chevronId: null, // access via trigger querySelector
      triggerId: "chart-pattern-dropdown-trigger",
    },
    {
      panelId: "sr-zone-dropdown-panel",
      chevronId: null,
      triggerId: "sr-zone-dropdown-trigger",
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
  // Skip if already initialized
  if (indicatorDropdownInitialized) return;

  const trigger = document.getElementById("indicator-dropdown-trigger");
  const panel = document.getElementById("indicator-dropdown-panel");
  const chevron = document.getElementById("indicator-chevron");

  if (!trigger || !panel) return;

  // Mark as initialized
  indicatorDropdownInitialized = true;

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

  // Update badge count when any indicator checkbox changes
  const updateBadge = () => {
    const badge = document.getElementById("indicator-count-badge");
    const count = ALL_INDICATOR_IDS.filter((id) => {
      const el = /** @type {HTMLInputElement | null} */ (
        document.getElementById(id)
      );
      return el?.checked;
    }).length;

    if (badge) {
      badge.textContent = count.toString();
      badge.classList.toggle("hidden", count === 0);
    }
  };

  // Add change listeners to all indicator checkboxes
  ALL_INDICATOR_IDS.forEach((id) => {
    document.getElementById(id)?.addEventListener("change", updateBadge);
  });
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

// Trigger chart display and initialization
function triggerChartDisplay(symbol) {
  document.getElementById("chart-tab-content-empty").classList.add("hidden");
  document
    .getElementById("chart-tab-content-container")
    .classList.remove("hidden");

  // Initialize dropdown and expand button after container is visible
  initIndicatorDropdown();
  initChartExpandButton();
  initPatternDropdown();
  initChartPatternDropdown();
  initSRZoneDropdown();

  initAdvancedChart(symbol);
}

// Initialize Advanced Chart
function initAdvancedChart(symbol) {
  currentChartSymbol = symbol;

  // Clear pattern markers when switching symbols
  displayedPatternMarkers.clear();
  markersPrimitive = null;

  // Clear pattern list UI
  clearPatternListUI();

  const timeframe =
    /** @type {HTMLSelectElement | null} */ (
      document.getElementById("chart-timeframe")
    )?.value || "1M";
  const interval =
    /** @type {HTMLSelectElement | null} */ (
      document.getElementById("chart-interval")
    )?.value || "1D";

  renderAdvancedChart(symbol, timeframe, interval);

  // Add event listeners for controls
  document.getElementById("chart-timeframe")?.addEventListener("change", () => {
    // Clear all pattern visualizations and reset UI before re-rendering
    clearAllPatternVisualizations();
    clearPatternListUI();

    renderAdvancedChart(
      currentChartSymbol,
      /** @type {HTMLSelectElement | null} */ (
        document.getElementById("chart-timeframe")
      )?.value || "1M",
      /** @type {HTMLSelectElement | null} */ (
        document.getElementById("chart-interval")
      )?.value || "1D",
    );
  });
  document.getElementById("chart-interval")?.addEventListener("change", () => {
    // Clear all pattern visualizations and reset UI before re-rendering
    clearAllPatternVisualizations();
    clearPatternListUI();

    renderAdvancedChart(
      currentChartSymbol,
      /** @type {HTMLSelectElement | null} */ (
        document.getElementById("chart-timeframe")
      )?.value || "1M",
      /** @type {HTMLSelectElement | null} */ (
        document.getElementById("chart-interval")
      )?.value || "1D",
    );
  });

  // Add event listeners for all indicator checkboxes
  ALL_INDICATOR_IDS.forEach((id) => {
    document.getElementById(id)?.addEventListener("change", () => {
      renderAdvancedChart(
        currentChartSymbol,
        /** @type {HTMLSelectElement | null} */ (
          document.getElementById("chart-timeframe")
        )?.value || "1M",
        /** @type {HTMLSelectElement | null} */ (
          document.getElementById("chart-interval")
        )?.value || "1D",
      );
    });
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
  indicatorSeries = [];
  indicatorValues = {};

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

  let data;
  try {
    const response = await fetch(
      `/chart/${symbol}?start=${currentChartStart}&end=${currentChartEnd}&interval=${apiInterval}`,
    );
    if (response.ok) {
      const result = await response.json();
      // Convert API data to chart format
      data = result.data.map((d) => ({
        x: new Date(d.time),
        o: d.open,
        h: d.high,
        l: d.low,
        c: d.close,
        v: d.volume,
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

  // Convert data to Lightweight Charts format (Unix timestamp in seconds)
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

  // Get price range for scaling oscillators
  const prices = data.map((d) => d.c);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const priceRange = maxPrice - minPrice;
  const priceMid = (maxPrice + minPrice) / 2;

  // Helper to add a line series
  const addLineSeries = (seriesData, options, pane = 0) => {
    const series = priceChart.addSeries(
      LightweightCharts.LineSeries,
      options,
      pane,
    );
    series.setData(seriesData);
    indicatorSeries.push(series);
    return series;
  };

  // =====================
  // MOVING AVERAGES
  // =====================

  if (isIndicatorEnabled("indicator-ma")) {
    const maData = calculateMA(data, 20)
      .map((v, i) => ({
        time: Math.floor(data[i].x.getTime() / 1000),
        value: v,
      }))
      .filter((d) => d.value !== null);
    addLineSeries(maData, {
      color: INDICATOR_CONFIG.ma.color,
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    maData.forEach((d) => {
      if (!indicatorValues[d.time]) indicatorValues[d.time] = {};
      indicatorValues[d.time].ma = d.value;
    });
  }

  if (isIndicatorEnabled("indicator-ema")) {
    const emaData = calculateEMA(data, 9)
      .map((v, i) => ({
        time: Math.floor(data[i].x.getTime() / 1000),
        value: v,
      }))
      .filter((d) => d.value !== null);
    addLineSeries(emaData, {
      color: INDICATOR_CONFIG.ema.color,
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    emaData.forEach((d) => {
      if (!indicatorValues[d.time]) indicatorValues[d.time] = {};
      indicatorValues[d.time].ema = d.value;
    });
  }

  if (isIndicatorEnabled("indicator-wma")) {
    const wmaData = calculateWMA(data, 20)
      .map((v, i) => ({
        time: Math.floor(data[i].x.getTime() / 1000),
        value: v,
      }))
      .filter((d) => d.value !== null);
    addLineSeries(wmaData, {
      color: INDICATOR_CONFIG.wma.color,
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    wmaData.forEach((d) => {
      if (!indicatorValues[d.time]) indicatorValues[d.time] = {};
      indicatorValues[d.time].wma = d.value;
    });
  }

  if (isIndicatorEnabled("indicator-vwap")) {
    const vwapData = calculateVWAP(data)
      .map((v, i) => ({
        time: Math.floor(data[i].x.getTime() / 1000),
        value: v,
      }))
      .filter((d) => d.value !== null);
    addLineSeries(vwapData, {
      color: INDICATOR_CONFIG.vwap.color,
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    vwapData.forEach((d) => {
      if (!indicatorValues[d.time]) indicatorValues[d.time] = {};
      indicatorValues[d.time].vwap = d.value;
    });
  }

  // =====================
  // BANDS / CHANNELS
  // =====================

  if (isIndicatorEnabled("indicator-bb")) {
    const bb = calculateBB(data, 20, 2);
    const upperData = bb
      .map((v, i) => ({
        time: Math.floor(data[i].x.getTime() / 1000),
        value: v.upper,
      }))
      .filter((d) => d.value !== null);
    const lowerData = bb
      .map((v, i) => ({
        time: Math.floor(data[i].x.getTime() / 1000),
        value: v.lower,
      }))
      .filter((d) => d.value !== null);

    addLineSeries(upperData, {
      color: INDICATOR_CONFIG.bb.color,
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    addLineSeries(lowerData, {
      color: INDICATOR_CONFIG.bb.color,
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    bb.forEach((v, i) => {
      if (v.upper !== null) {
        const time = Math.floor(data[i].x.getTime() / 1000);
        if (!indicatorValues[time]) indicatorValues[time] = {};
        indicatorValues[time].bbUpper = v.upper;
        indicatorValues[time].bbMiddle = v.middle;
        indicatorValues[time].bbLower = v.lower;
      }
    });
  }

  if (isIndicatorEnabled("indicator-atr")) {
    const atr = calculateATR(data, 14);
    // Scale ATR to visible range (overlay as offset from bottom of price range)
    const atrMax = Math.max(...atr.filter((v) => v !== null)) || 1;
    const atrData = atr
      .map((v, i) => ({
        time: Math.floor(data[i].x.getTime() / 1000),
        value: v === null ? null : minPrice + (v / atrMax) * priceRange * 0.3,
      }))
      .filter((d) => d.value !== null);
    addLineSeries(atrData, {
      color: INDICATOR_CONFIG.atr.color,
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dotted,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    atr.forEach((v, i) => {
      if (v !== null) {
        const time = Math.floor(data[i].x.getTime() / 1000);
        if (!indicatorValues[time]) indicatorValues[time] = {};
        indicatorValues[time].atr = v;
      }
    });
  }

  // =====================
  // OSCILLATORS
  // =====================

  if (isIndicatorEnabled("indicator-rsi")) {
    const rsi = calculateRSI(data, 14);
    const rsiData = rsi
      .map((v, i) => ({
        time: Math.floor(data[i].x.getTime() / 1000),
        value: v === null ? null : minPrice + (v / 100) * priceRange,
      }))
      .filter((d) => d.value !== null);
    addLineSeries(rsiData, {
      color: INDICATOR_CONFIG.rsi.color,
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dotted,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    rsi.forEach((v, i) => {
      if (v !== null) {
        const time = Math.floor(data[i].x.getTime() / 1000);
        if (!indicatorValues[time]) indicatorValues[time] = {};
        indicatorValues[time].rsi = v;
      }
    });
  }

  if (isIndicatorEnabled("indicator-macd")) {
    const macd = calculateMACD(data, 12, 26, 9);
    const macdValues = macd.macdLine.filter((v) => v !== null);
    const macdMax = Math.max(...macdValues.map(Math.abs)) || 1;
    const scaleMACD = (v) =>
      v === null ? null : priceMid + (v / macdMax) * (priceRange / 4);

    const macdData = macd.macdLine
      .map((v, i) => ({
        time: Math.floor(data[i].x.getTime() / 1000),
        value: scaleMACD(v),
      }))
      .filter((d) => d.value !== null);
    const signalData = macd.signalLine
      .map((v, i) => ({
        time: Math.floor(data[i].x.getTime() / 1000),
        value: scaleMACD(v),
      }))
      .filter((d) => d.value !== null);

    addLineSeries(macdData, {
      color: INDICATOR_CONFIG.macd.colors.line,
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    addLineSeries(signalData, {
      color: INDICATOR_CONFIG.macd.colors.signal,
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    macd.macdLine.forEach((v, i) => {
      if (
        v !== null ||
        macd.signalLine[i] !== null ||
        macd.histogram[i] !== null
      ) {
        const time = Math.floor(data[i].x.getTime() / 1000);
        if (!indicatorValues[time]) indicatorValues[time] = {};
        indicatorValues[time].macdLine = v;
        indicatorValues[time].macdSignal = macd.signalLine[i];
        indicatorValues[time].macdHist = macd.histogram[i];
      }
    });
  }

  if (isIndicatorEnabled("indicator-stoch")) {
    const stoch = calculateStochastic(data, 14, 3, 3);
    const stochK = stoch.k
      .map((v, i) => ({
        time: Math.floor(data[i].x.getTime() / 1000),
        value: v === null ? null : minPrice + (v / 100) * priceRange,
      }))
      .filter((d) => d.value !== null);
    const stochD = stoch.d
      .map((v, i) => ({
        time: Math.floor(data[i].x.getTime() / 1000),
        value: v === null ? null : minPrice + (v / 100) * priceRange,
      }))
      .filter((d) => d.value !== null);

    addLineSeries(stochK, {
      color: INDICATOR_CONFIG.stoch.colors.k,
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    addLineSeries(stochD, {
      color: INDICATOR_CONFIG.stoch.colors.d,
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    stoch.k.forEach((v, i) => {
      if (v !== null || stoch.d[i] !== null) {
        const time = Math.floor(data[i].x.getTime() / 1000);
        if (!indicatorValues[time]) indicatorValues[time] = {};
        indicatorValues[time].stochK = v;
        indicatorValues[time].stochD = stoch.d[i];
      }
    });
  }

  if (isIndicatorEnabled("indicator-williams")) {
    const willR = calculateWilliamsR(data, 14);
    const willRData = willR
      .map((v, i) => ({
        time: Math.floor(data[i].x.getTime() / 1000),
        value: v === null ? null : minPrice + ((v + 100) / 100) * priceRange,
      }))
      .filter((d) => d.value !== null);
    addLineSeries(willRData, {
      color: INDICATOR_CONFIG.williams.color,
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dotted,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    willR.forEach((v, i) => {
      if (v !== null) {
        const time = Math.floor(data[i].x.getTime() / 1000);
        if (!indicatorValues[time]) indicatorValues[time] = {};
        indicatorValues[time].williamsR = v;
      }
    });
  }

  if (isIndicatorEnabled("indicator-cci")) {
    const cci = calculateCCI(data, 20);
    const cciMax =
      Math.max(...cci.filter((v) => v !== null).map(Math.abs)) || 100;
    const cciData = cci
      .map((v, i) => ({
        time: Math.floor(data[i].x.getTime() / 1000),
        value: v === null ? null : priceMid + (v / cciMax) * (priceRange / 4),
      }))
      .filter((d) => d.value !== null);
    addLineSeries(cciData, {
      color: INDICATOR_CONFIG.cci.color,
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dotted,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    cci.forEach((v, i) => {
      if (v !== null) {
        const time = Math.floor(data[i].x.getTime() / 1000);
        if (!indicatorValues[time]) indicatorValues[time] = {};
        indicatorValues[time].cci = v;
      }
    });
  }

  if (isIndicatorEnabled("indicator-roc")) {
    const roc = calculateROC(data, 10);
    const rocMax =
      Math.max(...roc.filter((v) => v !== null).map(Math.abs)) || 10;
    const rocData = roc
      .map((v, i) => ({
        time: Math.floor(data[i].x.getTime() / 1000),
        value: v === null ? null : priceMid + (v / rocMax) * (priceRange / 4),
      }))
      .filter((d) => d.value !== null);
    addLineSeries(rocData, {
      color: INDICATOR_CONFIG.roc.color,
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dotted,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    roc.forEach((v, i) => {
      if (v !== null) {
        const time = Math.floor(data[i].x.getTime() / 1000);
        if (!indicatorValues[time]) indicatorValues[time] = {};
        indicatorValues[time].roc = v;
      }
    });
  }

  // =====================
  // TREND
  // =====================

  if (isIndicatorEnabled("indicator-adx")) {
    const adxResult = calculateADX(data, 14);
    const adxMax = Math.max(...adxResult.adx.filter((v) => v !== null)) || 50;
    const scaleADX = (v) =>
      v === null ? null : minPrice + (v / adxMax) * priceRange * 0.5;

    const adxData = adxResult.adx
      .map((v, i) => ({
        time: Math.floor(data[i].x.getTime() / 1000),
        value: scaleADX(v),
      }))
      .filter((d) => d.value !== null);
    const plusDIData = adxResult.plusDI
      .map((v, i) => ({
        time: Math.floor(data[i].x.getTime() / 1000),
        value: scaleADX(v),
      }))
      .filter((d) => d.value !== null);
    const minusDIData = adxResult.minusDI
      .map((v, i) => ({
        time: Math.floor(data[i].x.getTime() / 1000),
        value: scaleADX(v),
      }))
      .filter((d) => d.value !== null);

    addLineSeries(adxData, {
      color: INDICATOR_CONFIG.adx.colors.adx,
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    addLineSeries(plusDIData, {
      color: INDICATOR_CONFIG.adx.colors.plusDI,
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    addLineSeries(minusDIData, {
      color: INDICATOR_CONFIG.adx.colors.minusDI,
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    adxResult.adx.forEach((v, i) => {
      if (v !== null) {
        const time = Math.floor(data[i].x.getTime() / 1000);
        if (!indicatorValues[time]) indicatorValues[time] = {};
        indicatorValues[time].adx = v;
        indicatorValues[time].plusDI = adxResult.plusDI[i];
        indicatorValues[time].minusDI = adxResult.minusDI[i];
      }
    });
  }

  // =====================
  // VOLUME INDICATORS
  // =====================

  if (isIndicatorEnabled("indicator-vol-sma")) {
    const volSmaData = calculateVolumeSMA(data, 20)
      .map((v, i) => ({
        time: Math.floor(data[i].x.getTime() / 1000),
        value: v,
      }))
      .filter((d) => d.value !== null);
    addLineSeries(
      volSmaData,
      {
        color: INDICATOR_CONFIG.volSma.color,
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: false,
      },
      1,
    );
    volSmaData.forEach((d) => {
      if (!indicatorValues[d.time]) indicatorValues[d.time] = {};
      indicatorValues[d.time].volSma = d.value;
    });
  }

  if (isIndicatorEnabled("indicator-obv")) {
    const obv = calculateOBV(data);
    // Scale OBV to fit volume pane
    const obvMax = Math.max(...obv.map(Math.abs)) || 1;
    const volMax = Math.max(...data.map((d) => d.v)) || 1;
    const obvData = obv
      .map((v, i) => ({
        time: Math.floor(data[i].x.getTime() / 1000),
        value: (v / obvMax) * volMax * 0.8,
      }))
      .filter((d) => d.value !== null);
    addLineSeries(
      obvData,
      {
        color: INDICATOR_CONFIG.obv.color,
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: false,
      },
      1,
    );
    obv.forEach((v, i) => {
      const time = Math.floor(data[i].x.getTime() / 1000);
      if (!indicatorValues[time]) indicatorValues[time] = {};
      indicatorValues[time].obv = v;
    });
  }

  if (isIndicatorEnabled("indicator-mfi")) {
    const mfi = calculateMFI(data, 14);
    const volMax = Math.max(...data.map((d) => d.v)) || 1;
    const mfiData = mfi
      .map((v, i) => ({
        time: Math.floor(data[i].x.getTime() / 1000),
        value: v === null ? null : (v / 100) * volMax * 0.8,
      }))
      .filter((d) => d.value !== null);
    addLineSeries(
      mfiData,
      {
        color: INDICATOR_CONFIG.mfi.color,
        lineWidth: 1,
        lineStyle: LightweightCharts.LineStyle.Dotted,
        priceLineVisible: false,
        lastValueVisible: false,
      },
      1,
    );
    mfi.forEach((v, i) => {
      if (v !== null) {
        const time = Math.floor(data[i].x.getTime() / 1000);
        if (!indicatorValues[time]) indicatorValues[time] = {};
        indicatorValues[time].mfi = v;
      }
    });
  }

  if (isIndicatorEnabled("indicator-cmf")) {
    const cmf = calculateCMF(data, 20);
    const volMax = Math.max(...data.map((d) => d.v)) || 1;
    const cmfData = cmf
      .map((v, i) => ({
        time: Math.floor(data[i].x.getTime() / 1000),
        value: v === null ? null : (v + 1) * 0.5 * volMax * 0.8,
      }))
      .filter((d) => d.value !== null);
    addLineSeries(
      cmfData,
      {
        color: INDICATOR_CONFIG.cmf.color,
        lineWidth: 1,
        lineStyle: LightweightCharts.LineStyle.Dotted,
        priceLineVisible: false,
        lastValueVisible: false,
      },
      1,
    );
    cmf.forEach((v, i) => {
      if (v !== null) {
        const time = Math.floor(data[i].x.getTime() / 1000);
        if (!indicatorValues[time]) indicatorValues[time] = {};
        indicatorValues[time].cmf = v;
      }
    });
  }

  // =====================
  // PIVOT POINTS
  // =====================
  if (isIndicatorEnabled("indicator-pivot")) {
    const pp = calculatePivotPoints(data[data.length - 1]);
    const colors = INDICATOR_CONFIG.pivot.colors;
    const addPivotLine = (price, color, title) => {
      if (price && !isNaN(price)) {
        candleSeries.createPriceLine({
          price: price,
          color: color,
          lineWidth: 1,
          lineStyle: LightweightCharts.LineStyle.Dashed,
          axisLabelVisible: true,
          title: title,
        });
      }
    };
    addPivotLine(pp.pivot, colors.pivot, "P");
    addPivotLine(pp.r1, colors.resistance, "R1");
    addPivotLine(pp.r2, colors.resistance, "R2");
    addPivotLine(pp.r3, colors.resistance, "R3");
    addPivotLine(pp.s1, colors.support, "S1");
    addPivotLine(pp.s2, colors.support, "S2");
    addPivotLine(pp.s3, colors.support, "S3");
  }

  // =====================
  // FIBONACCI LEVELS
  // =====================
  if (isIndicatorEnabled("indicator-fib")) {
    const fib = calculateFibonacciLevels(data, 50);
    const colors = INDICATOR_CONFIG.fib.colors;
    const addFibLine = (price, color, title) => {
      if (price && !isNaN(price)) {
        candleSeries.createPriceLine({
          price: price,
          color: color,
          lineWidth: 1,
          lineStyle: LightweightCharts.LineStyle.Dotted,
          axisLabelVisible: true,
          title: title,
        });
      }
    };
    addFibLine(fib.level_0, colors.key, "0%");
    addFibLine(fib.level_236, colors.level, "23.6%");
    addFibLine(fib.level_382, colors.key, "38.2%");
    addFibLine(fib.level_500, colors.key, "50%");
    addFibLine(fib.level_618, colors.key, "61.8%");
    addFibLine(fib.level_786, colors.level, "78.6%");
    addFibLine(fib.level_100, colors.key, "100%");
  }

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

      // Add indicator values using shared utility
      tooltipContent += renderTooltipIndicators(
        indicatorValues,
        param.time,
        INDICATOR_CONFIG,
      );

      // Add volume indicators if exists
      const volIndicators = renderTooltipIndicators(
        indicatorValues,
        param.time,
        INDICATOR_CONFIG,
        true,
      );
      if (volIndicators) {
        tooltipContent += volIndicators;
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
        const supportLine = priceChart.addSeries(LightweightCharts.LineSeries, {
          color: "#22c55e",
          lineWidth: 2,
          lineStyle: LightweightCharts.LineStyle.Dashed,
          priceLineVisible: false,
          lastValueVisible: false,
        });
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
      const keyPointsLine = priceChart.addSeries(LightweightCharts.LineSeries, {
        color: lineColor,
        lineWidth: 2,
        priceLineVisible: false,
        lastValueVisible: false,
      });
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
    item.classList.add("border-blue-500", "dark:border-blue-400");
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
    itemEl.classList.remove("border-blue-500", "dark:border-blue-400");
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
    itemEl.classList.add("border-blue-500", "dark:border-blue-400");
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
}
