// Chart Module - Global chart instances for cleanup (Lightweight Charts)
let priceChart = null;
let candleSeries = null;
let volumeSeries = null;
let indicatorSeries = []; // Array to hold indicator line series
let indicatorValues = {}; // Store raw indicator values mapping time -> {key: value}
let currentChartSymbol = null;

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
    panel.classList.toggle("hidden");
    chevron?.classList.toggle("rotate-180", !isOpen);
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

    // Trigger resize for charts after layout change
    setTimeout(() => {
      window.dispatchEvent(new Event("resize"));
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

  initAdvancedChart(symbol);
}

// Initialize Advanced Chart
function initAdvancedChart(symbol) {
  currentChartSymbol = symbol;
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
  const startStr = formatDate(start);
  const endStr = formatDate(end);

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
      `/chart/${symbol}?start=${startStr}&end=${endStr}&interval=${apiInterval}`,
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
    window.dispatchEvent(new Event("resize"));
    refreshCharts();
  }, 50);
}
