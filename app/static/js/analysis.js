/**
 * Analysis Module - Handles technical analysis display and charts
 */

// --- State ---
let lastFetchedTechnicalSymbol = null;

/**
 * Reset analysis state when stock changes
 */
function resetAnalysisState() {
  lastFetchedTechnicalSymbol = null;
  clearAnalysisDisplay();
}

/**
 * Check if analysis needs to be fetched for the current stock
 * @param {string} symbol - Stock symbol
 * @returns {boolean}
 */
function shouldFetchAnalysis(symbol) {
  return symbol && symbol !== lastFetchedTechnicalSymbol;
}

/**
 * Trigger analysis fetch when switching to analysis tab or selecting a new stock
 * @param {string} symbol - Stock symbol
 * @param {string} companyName - Company name
 */
function triggerTechnicalAnalysis(symbol, companyName) {
  if (shouldFetchAnalysis(symbol)) {
    fetchTechnicalAnalysis(symbol, companyName);
    lastFetchedTechnicalSymbol = symbol;
  }
}

/**
 * Handle Analysis Tab switch logic
 * @param {string} symbol - Current selected stock symbol
 * @param {string} companyName - Current selected stock company name
 */
function handleAnalysisTabSwitch(symbol, companyName) {
  if (lastFetchedTechnicalSymbol) {
    document
      .getElementById("analysis-content-timeframe")
      ?.classList.remove("hidden");
    document
      .getElementById("analysis-chart-collapsible")
      ?.classList.remove("hidden");
  }

  triggerTechnicalAnalysis(symbol, companyName);
}

// Analysis chart instances (separate from main chart)
let analysisChart = null;
let analysisCandleSeries = null;
let analysisVolumeSeries = null;

// Sparkline charts storage
let sparklineCharts = {};

/**
 * Refresh analysis chart by fitting content to time scale
 */
function refreshAnalysisChart() {
  if (typeof analysisChart !== "undefined" && analysisChart)
    analysisChart.timeScale().fitContent();
}

/**
 * Toggle Analysis Chart visibility
 */
function toggleAnalysisChart() {
  const wrapper = document.getElementById("analysis-chart-wrapper");
  const analysisIcon = document.getElementById("analysis-chart-toggle-icon");

  if (wrapper) {
    wrapper.classList.toggle("collapsed");
    if (analysisIcon) {
      analysisIcon.style.transform = wrapper.classList.contains("collapsed")
        ? "rotate(180deg)"
        : "rotate(0deg)";
    }
  }
  refreshAnalysisChart();
}

/**
 * Initialize Analysis Chart Resizer
 */
function initAnalysisChartResizer() {
  const analysisChartResizer = document.getElementById(
    "analysis-chart-resizer",
  );
  const analysisChartContainer = document.getElementById(
    "analysis-price-chart-container",
  );

  let isResizingAnalysisChart = false;

  if (analysisChartResizer && analysisChartContainer) {
    analysisChartResizer.addEventListener("mousedown", (e) => {
      isResizingAnalysisChart = true;
      analysisChartResizer.classList.add("resizing");
      document.body.style.cursor = "ns-resize";
      document.body.classList.add("select-none");
    });

    document.addEventListener("mousemove", (e) => {
      if (!isResizingAnalysisChart) return;

      const rect = analysisChartContainer.getBoundingClientRect();
      const newHeight = e.clientY - rect.top;

      // Constraints: Min 200px, Max 800px
      if (newHeight >= 200 && newHeight <= 800) {
        analysisChartContainer.style.height = `${newHeight}px`;
        // Call fitContent during resizing for real-time scaling
        if (typeof analysisChart !== "undefined" && analysisChart) {
          analysisChart.timeScale().fitContent();
        }
      }
    });

    document.addEventListener("mouseup", () => {
      if (isResizingAnalysisChart) {
        isResizingAnalysisChart = false;
        analysisChartResizer.classList.remove("resizing");
        document.body.style.cursor = "default";
        document.body.classList.remove("select-none");

        // Optional: Save height preference
        localStorage.setItem(
          "analysis-chart-height",
          analysisChartContainer.style.height,
        );
      }
    });

    // Load saved height if exists
    const savedHeight = localStorage.getItem("analysis-chart-height");
    if (savedHeight) {
      analysisChartContainer.style.height = savedHeight;
    }
  }
}

/**
 * Render Analysis Chart (separate chart for Analysis tab)
 * @param {Array} ohlcv_data - OHLCV data
 */
async function renderAnalysisChart(ohlcv_data) {
  const chartContainer = document.getElementById("analysis-candlestick-chart");
  if (!chartContainer) return;

  // Destroy previous instance
  if (analysisChart) {
    analysisChart.remove();
    analysisChart = null;
  }
  analysisCandleSeries = null;
  analysisVolumeSeries = null;

  // Remove skeleton and show chart
  chartContainer.innerHTML = "";
  chartContainer.classList.remove("hidden");

  const isDark = document.documentElement.classList.contains("dark");
  const theme = isDark
    ? {
        layout: {
          background: { type: "solid", color: "#0f172a" },
          textColor: "#94a3b8",
        },
        grid: {
          vertLines: { color: "rgba(148, 163, 184, 0.1)" },
          horzLines: { color: "rgba(148, 163, 184, 0.1)" },
        },
        rightPriceScale: { borderColor: "rgba(148, 163, 184, 0.2)" },
        timeScale: { borderColor: "rgba(148, 163, 184, 0.2)" },
      }
    : {
        layout: {
          background: { type: "solid", color: "#ffffff" },
          textColor: "#334155",
        },
        grid: {
          vertLines: { color: "rgba(100, 116, 139, 0.1)" },
          horzLines: { color: "rgba(100, 116, 139, 0.1)" },
        },
        rightPriceScale: { borderColor: "rgba(100, 116, 139, 0.2)" },
        timeScale: { borderColor: "rgba(100, 116, 139, 0.2)" },
      };

  analysisChart = LightweightCharts.createChart(chartContainer, {
    autoSize: true,
    ...theme,
    timeScale: { ...theme.timeScale, timeVisible: false },
  });

  // Convert data to Lightweight Charts format (Unix timestamp in seconds)
  const volumeData = ohlcv_data.map((d) => ({
    time: d.time,
    value: d.volume,
    color:
      d.close >= d.open ? "rgba(16, 185, 129, 0.6)" : "rgba(239, 68, 68, 0.6)",
  }));

  analysisCandleSeries = analysisChart.addSeries(
    LightweightCharts.CandlestickSeries,
    {
      upColor: CONFIG.COLORS.UP,
      downColor: CONFIG.COLORS.DOWN,
      borderUpColor: CONFIG.COLORS.UP,
      borderDownColor: CONFIG.COLORS.DOWN,
      wickUpColor: CONFIG.COLORS.UP,
      wickDownColor: CONFIG.COLORS.DOWN,
    },
  );
  analysisCandleSeries.setData(ohlcv_data);

  analysisVolumeSeries = analysisChart.addSeries(
    LightweightCharts.HistogramSeries,
    {
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    },
    1,
  );
  analysisVolumeSeries.setData(volumeData);

  analysisChart.panes()[1]?.setHeight(50);

  // Create tooltip element
  const tooltip = document.createElement("div");
  tooltip.className = "analysis-chart-tooltip";
  Object.assign(tooltip.style, {
    position: "absolute",
    display: "none",
    padding: "10px 14px",
    background: isDark ? "rgba(30, 41, 59, 0.95)" : "rgba(255, 255, 255, 0.95)",
    color: isDark ? "#e2e8f0" : "#1e293b",
    fontSize: "12px",
    fontFamily: "sans-serif",
    lineHeight: "1.5",
    borderRadius: "8px",
    zIndex: "100",
    pointerEvents: "none",
    backdropFilter: "blur(8px)",
    border: isDark
      ? "1px solid rgba(148, 163, 184, 0.2)"
      : "1px solid rgba(100, 116, 139, 0.2)",
    boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
    whiteSpace: "nowrap",
  });
  chartContainer.style.position = "relative";
  chartContainer.appendChild(tooltip);

  // Subscribe to crosshair move
  analysisChart.subscribeCrosshairMove((param) => {
    if (
      param.point === undefined ||
      !param.time ||
      param.point.x < 0 ||
      param.point.x > chartContainer.clientWidth ||
      param.point.y < 0 ||
      param.point.y > chartContainer.clientHeight
    ) {
      tooltip.style.display = "none";
      return;
    }

    const candleData = /** @type {ICandleData | undefined} */ (
      param.seriesData.get(analysisCandleSeries)
    );
    const volumeData = /** @type {IVolumeData | undefined} */ (
      param.seriesData.get(analysisVolumeSeries)
    );

    if (candleData) {
      const changePercent = (
        ((candleData.close - candleData.open) / candleData.open) *
        100
      ).toFixed(2);
      const changeColor =
        candleData.close >= candleData.open ? "#10b981" : "#ef4444";
      const changeSign = candleData.close >= candleData.open ? "+" : "";

      tooltip.innerHTML = `
        <div style="margin-bottom: 6px; font-weight: 500; opacity: 0.8;">${formatDate(
          param.time,
        )}</div>
        <div><span style="opacity: 0.6;">Open:</span> <strong>${formatPrice(
          candleData.open,
        )}</strong></div>
        <div><span style="opacity: 0.6;">High:</span> <strong>${formatPrice(
          candleData.high,
        )}</strong></div>
        <div><span style="opacity: 0.6;">Low:</span> <strong>${formatPrice(
          candleData.low,
        )}</strong></div>
        <div><span style="opacity: 0.6;">Close:</span> <strong>${formatPrice(
          candleData.close,
        )}</strong> <span style="color: ${changeColor};">(${changeSign}${changePercent}%)</span></div>
        ${
          volumeData?.value
            ? `<div><span style="opacity: 0.6;">Volume:</span> <strong>${formatNumber(
                volumeData.value,
                2,
                true,
              )}</strong></div>`
            : ""
        }
      `;

      tooltip.style.display = "block";

      // Position tooltip
      const tooltipWidth = tooltip.offsetWidth || 150;
      const tooltipHeight = tooltip.offsetHeight || 100;
      let left = param.point.x + 15;
      let top = param.point.y + 15;

      if (left + tooltipWidth > chartContainer.clientWidth) {
        left = param.point.x - tooltipWidth - 15;
      }
      if (top + tooltipHeight > chartContainer.clientHeight) {
        top = param.point.y - tooltipHeight - 15;
      }
      if (left < 0) left = 10;
      if (top < 0) top = 10;

      tooltip.style.left = left + "px";
      tooltip.style.top = top + "px";
    } else {
      tooltip.style.display = "none";
    }
  });

  setTimeout(() => {
    window.dispatchEvent(new Event("resize"));
    refreshAnalysisChart();
  }, 50);
}

/**
 * Draw sparkline chart for indicators
 * @param {string} containerId - Container element ID
 * @param {Array} data - Chart data
 * @param {string} color - Line color
 */
function drawSparkline(containerId, data, color) {
  const container = document.getElementById(containerId);
  if (!container) return;

  // Clear skeleton loading state
  removeSkeleton(containerId);

  if (!data || data.length === 0) return;

  // Clear existing chart if any to avoid leaks/visual bugs
  if (sparklineCharts[containerId]) {
    try {
      sparklineCharts[containerId].remove();
      delete sparklineCharts[containerId];
    } catch (e) {
      console.error("Error removing chart:", e);
    }
  }

  const isDark = document.documentElement.classList.contains("dark");
  const chart = LightweightCharts.createChart(container, {
    layout: {
      background: { type: "solid", color: "transparent" },
      textColor: isDark ? "#94a3b8" : "#64748b",
      fontSize: 10,
    },
    grid: {
      vertLines: { visible: false },
      horzLines: { visible: false },
    },
    timeScale: {
      visible: false,
      borderVisible: false,
    },
    rightPriceScale: {
      visible: false,
      borderVisible: false,
    },
    handleScroll: false,
    handleScale: false,
    crosshair: {
      vertLine: {
        color: isDark ? "rgba(255, 255, 255, 0.3)" : "rgba(0, 0, 0, 0.2)",
        width: 1,
        style: 2,
      },
      horzLine: { visible: false },
    },
  });

  const series = chart.addSeries(LightweightCharts.AreaSeries, {
    lineColor: color,
    topColor: color.replace(/, 1\)$/, ", 0.2)"),
    bottomColor: color.replace(/, 1\)$/, ", 0)"),
    lineWidth: 2,
    priceLineVisible: false,
    lastValueVisible: false,
    crosshairMarkerVisible: true,
    autoscaleInfoProvider: () => {
      const values = data.map((d) => (typeof d === "object" ? d.value : d));
      const min = Math.min(...values);
      const max = Math.max(...values);
      const margin = (max - min) * 0.1;
      return {
        priceRange: {
          minValue: min - margin,
          maxValue: max + margin,
        },
      };
    },
  });

  // Prepare data (handle both simple values and objects with time)
  const chartData = data.map((d, i) => {
    if (typeof d === "object" && d.time) return d;
    return { time: i, value: d };
  });

  series.setData(chartData);
  chart.timeScale().fitContent();

  // Add Simple Tooltip
  const tooltip = document.createElement("div");
  tooltip.className = "sparkline-tooltip";
  Object.assign(tooltip.style, {
    position: "absolute",
    display: "none",
    padding: "4px 8px",
    background: isDark ? "rgba(15, 23, 42, 0.95)" : "rgba(255, 255, 255, 0.95)",
    color: isDark ? "#f1f5f9" : "#1e293b",
    fontSize: "11px",
    fontWeight: "bold",
    borderRadius: "6px",
    zIndex: "100",
    pointerEvents: "none",
    backdropFilter: "blur(8px)",
    border: isDark
      ? "1px solid rgba(255,255,255,0.1)"
      : "1px solid rgba(0,0,0,0.1)",
    boxShadow: "0 4px 12px rgba(0,0,0,0.3)",
    whiteSpace: "nowrap",
    lineHeight: "1.2",
    textAlign: "center",
  });
  container.appendChild(tooltip);

  chart.subscribeCrosshairMove((param) => {
    if (
      param.point === undefined ||
      !param.time ||
      param.point.x < 0 ||
      param.point.x > container.clientWidth ||
      param.point.y < 0 ||
      param.point.y > container.clientHeight
    ) {
      tooltip.style.display = "none";
    } else {
      const seriesData = /** @type {IVolumeData | undefined} */ (
        param.seriesData.get(series)
      );
      const value = seriesData ? seriesData.value : undefined;
      if (value !== undefined) {
        tooltip.style.display = "block";
        tooltip.innerHTML = `
          <div style="font-size: 9px; opacity: 0.6; font-weight: medium; margin-bottom: 2px;">${formatDate(
            param.time,
          )}</div>
          <div>${formatNumber(value, 2)}</div>
        `;

        const tooltipWidth = tooltip.offsetWidth || 50;
        const tooltipHeight = tooltip.offsetHeight || 25;
        let x = param.point.x + 10;
        let y = param.point.y + 10;

        if (x + tooltipWidth > container.clientWidth) {
          x = param.point.x - tooltipWidth - 10;
        }
        if (y + tooltipHeight > container.clientHeight) {
          y = param.point.y - tooltipHeight - 10;
        }
        if (x < 0) {
          x = 10;
        }
        if (y < 0) {
          y = 10;
        }

        tooltip.style.left = x + "px";
        tooltip.style.top = y + "px";
      } else {
        tooltip.style.display = "none";
      }
    }
  });

  sparklineCharts[containerId] = chart;
}

// Initialize on DOM content loaded
document.addEventListener("DOMContentLoaded", () => {
  initAnalysisChartResizer();
});

/**
 * Fetch and display technical analysis for a stock
 * @param {string} symbol - Stock symbol
 * @param {string} companyName - Company name
 */
async function fetchTechnicalAnalysis(symbol, companyName) {
  document.getElementById("analysis-tab-content-empty").classList.add("hidden");
  document
    .getElementById("analysis-tab-content-container")
    .classList.remove("hidden");
  document
    .getElementById("analysis-content-timeframe")
    .classList.remove("hidden");
  document
    .getElementById("analysis-chart-collapsible")
    .classList.remove("hidden");

  const analysisContentEl = document.getElementById("tech-analysis-content");
  const badge = document.getElementById("tech-recommendation-badge");

  let accumulatedText = "";

  try {
    const response = await fetch("/technical-analysis", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbol: symbol, company_name: companyName }),
    });

    if (!response.ok)
      throw new Error("API Connection Error: " + response.status);

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    let isFirstChunk = false;

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
            accumulatedText += evt.chunk;
            if (analysisContentEl) {
              analysisContentEl.innerHTML =
                processContentNoTickers(accumulatedText);
            }
          } else if (evt.type === "recommendation") {
            // Update recommendation badge
            if (badge) {
              badge.innerHTML = `<i data-lucide="sparkles" class="w-3.5 h-3.5 text-current"></i> ${evt.label}`;
              badge.classList.remove("opacity-0", "scale-95");
              badge.classList.add(
                "opacity-100",
                "scale-100",
                "animate-fade-in",
              );

              badge.classList.remove(
                "bg-slate-50",
                "dark:bg-slate-800",
                "text-slate-500",
                "dark:text-slate-400",
                "border-slate-200",
                "dark:border-slate-700",
              );

              const color = evt.color;
              if (color === "emerald" || color === "green") {
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
              } else if (color === "rose" || color === "red") {
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
              } else if (color === "yellow") {
                badge.classList.add(
                  "bg-gradient-to-b",
                  "from-amber-50",
                  "to-amber-100/90",
                  "dark:from-amber-500/10",
                  "dark:to-amber-500/30",
                  "text-amber-700",
                  "dark:text-amber-300",
                  "border-amber-200",
                  "dark:border-amber-500/40",
                );
              }
              lucide.createIcons({ root: badge });
            }
          } else if (evt.type === "data") {
            // Update indicator cards with data (default to short_term)
            const shortTerm = evt.short_term || {};
            const longTerm = evt.long_term || {};

            // Initialize display with short-term data
            const indicators = shortTerm.indicators || {};
            const methods = shortTerm.methods || [];
            const gauges = shortTerm.gauges || {};
            const ohlcv = shortTerm.ohlcv || [];
            updateIndicatorsDisplay(indicators, methods, gauges, ohlcv);

            // Setup timeframe card switching
            const cardShort = document.getElementById("tech-card-short");
            const cardLong = document.getElementById("tech-card-long");

            if (cardShort && cardLong) {
              const activeShortClass =
                "cursor-pointer transition-all duration-300 p-4 rounded-3xl border-2 border-indigo-400/60 bg-gradient-to-br from-indigo-100 via-indigo-50 to-purple-100 dark:from-indigo-600/30 dark:via-indigo-500/20 dark:to-purple-600/20 backdrop-blur-xl shadow-[0_8px_32px_rgba(99,102,241,0.3)] scale-[1.03] z-10";
              const inactiveShortClass =
                "cursor-pointer transition-all duration-300 p-4 rounded-3xl border border-slate-200 dark:border-white/10 bg-gradient-to-br from-slate-100 via-white to-slate-50 dark:from-slate-800/60 dark:via-slate-900/40 dark:to-slate-800/40 backdrop-blur-md shadow-sm opacity-60 hover:opacity-100 hover:scale-[1.01]";

              const activeLongClass =
                "cursor-pointer transition-all duration-300 p-4 rounded-3xl border-2 border-emerald-400/60 bg-gradient-to-br from-emerald-100 via-emerald-50 to-teal-100 dark:from-emerald-600/30 dark:via-emerald-500/20 dark:to-teal-600/20 backdrop-blur-xl shadow-[0_8px_32px_rgba(16,185,129,0.3)] scale-[1.03] z-10";
              const inactiveLongClass =
                "cursor-pointer transition-all duration-300 p-4 rounded-3xl border border-slate-200 dark:border-white/10 bg-gradient-to-br from-slate-100 via-white to-slate-50 dark:from-slate-800/60 dark:via-slate-900/40 dark:to-slate-800/40 backdrop-blur-md shadow-sm opacity-60 hover:opacity-100 hover:scale-[1.01]";

              cardShort.onclick = () => {
                cardShort.className = activeShortClass;
                cardLong.className = inactiveLongClass;
                updateIndicatorsDisplay(
                  shortTerm.indicators || {},
                  shortTerm.methods || [],
                  shortTerm.gauges || {},
                  shortTerm.ohlcv || [],
                );
              };
              cardLong.onclick = () => {
                cardLong.className = activeLongClass;
                cardShort.className = inactiveShortClass;
                updateIndicatorsDisplay(
                  longTerm.indicators || {},
                  longTerm.methods || [],
                  longTerm.gauges || {},
                  longTerm.ohlcv || [],
                );
              };
            }
          } else if (evt.type === "analysis_summary") {
            handleAnalysisSummary(evt.summary);
          } else if (evt.type === "error") {
            console.error("Stream Error:", evt.message);
            if (analysisContentEl)
              analysisContentEl.innerHTML += `<div class="text-red-500 text-xs mt-2">⚠️ ${evt.message}</div>`;
          }
        } catch (parseErr) {
          console.error("JSON Parse Error:", parseErr);
          if (analysisContentEl)
            analysisContentEl.innerHTML += `<div class="text-red-500 text-xs mt-2">⚠️ ${parseErr}</div>`;
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
  }
}

/**
 * Update indicators display with data
 * @param {Object} ind - Indicators data
 * @param {Array} meth - Methods array
 * @param {Object} gauges - Gauges data
 * @param {Array} ohlcv_data - OHLCV data
 */
function updateIndicatorsDisplay(ind, meth, gauges, ohlcv_data) {
  // RSI
  const rsiData = ind.rsi || {};
  const rsiValue = typeof rsiData === "object" ? rsiData.value : rsiData;
  if (rsiValue !== null && rsiValue !== undefined) {
    removeSkeleton("tech-rsi-value");
    updateValueWithTooltip("tech-rsi-value", formatNumber(rsiValue, 1));
    const marker = document.getElementById("tech-rsi-marker");
    if (marker) marker.style.left = `calc(${rsiValue}% - 8px)`;
    const rsiBarSkeleton = document.getElementById("tech-rsi-bar-skeleton");
    if (rsiBarSkeleton) rsiBarSkeleton.remove();

    const rsiSignal = document.getElementById("tech-rsi-signal");
    if (rsiSignal) {
      removeSkeleton("tech-rsi-signal");
      rsiSignal.className =
        "text-sm font-bold px-3 py-1 rounded-full flex items-center justify-center ml-auto";
      if (rsiValue < 30) {
        rsiSignal.textContent = "Quá bán";
        rsiSignal.classList.add(
          "bg-green-100",
          "text-green-700",
          "dark:bg-green-500/20",
          "dark:text-green-400",
        );
      } else if (rsiValue > 70) {
        rsiSignal.textContent = "Quá mua";
        rsiSignal.classList.add(
          "bg-red-100",
          "text-red-700",
          "dark:bg-red-500/20",
          "dark:text-red-400",
        );
      } else {
        rsiSignal.textContent = "Trung tính";
        rsiSignal.classList.add(
          "bg-yellow-100",
          "text-yellow-700",
          "dark:bg-yellow-500/20",
          "dark:text-yellow-400",
        );
      }
    }
  } else {
    removeSkeleton("tech-rsi-value");
    removeSkeleton("tech-rsi-signal");
  }

  // Stochastic
  const stoch = ind.stochastic || {};
  const stochK = document.getElementById("tech-stoch-k");
  const stochD = document.getElementById("tech-stoch-d");
  const stochSignal = document.getElementById("tech-stoch-signal");
  if (stochK) {
    removeSkeleton("tech-stoch-k");
    updateValueWithTooltip("tech-stoch-k", formatNumber(stoch.k, 1));
  }
  if (stochD) {
    removeSkeleton("tech-stoch-d");
    updateValueWithTooltip("tech-stoch-d", formatNumber(stoch.d, 1));
  }
  if (stochSignal && stoch.k !== null) {
    removeSkeleton("tech-stoch-signal");
    stochSignal.className =
      "text-sm font-bold px-3 py-1 rounded-full flex items-center justify-center";
    if (stoch.k < 20) {
      stochSignal.textContent = "Quá bán";
      stochSignal.classList.add(
        "bg-green-100",
        "text-green-700",
        "dark:bg-green-500/20",
        "dark:text-green-400",
      );
    } else if (stoch.k > 80) {
      stochSignal.textContent = "Quá mua";
      stochSignal.classList.add(
        "bg-red-100",
        "text-red-700",
        "dark:bg-red-500/20",
        "dark:text-red-400",
      );
    } else {
      stochSignal.textContent = "Trung tính";
      stochSignal.classList.add(
        "bg-yellow-100",
        "text-yellow-700",
        "dark:bg-yellow-500/20",
        "dark:text-yellow-400",
      );
    }
  }

  // Williams %R
  if (ind.willr !== undefined) {
    removeSkeleton("tech-willr");
    updateValueWithTooltip("tech-willr", formatNumber(ind.willr, 1));
  }

  // MACD
  const macd = ind.macd || {};
  const macdLine = document.getElementById("tech-macd-line");
  const macdSignalVal = document.getElementById("tech-macd-signal-val");
  const macdHist = document.getElementById("tech-macd-hist");
  const macdSignal = document.getElementById("tech-macd-signal");
  if (macdLine) {
    removeSkeleton("tech-macd-line");
    updateValueWithTooltip("tech-macd-line", formatNumber(macd.line));
  }
  if (macdSignalVal) {
    removeSkeleton("tech-macd-signal-val");
    updateValueWithTooltip("tech-macd-signal-val", formatNumber(macd.signal));
  }
  if (macdHist) {
    removeSkeleton("tech-macd-hist");
    updateValueWithTooltip("tech-macd-hist", formatNumber(macd.histogram));
    if (macd.histogram !== null) {
      macdHist.classList.remove(
        "text-green-600",
        "text-red-600",
        "dark:text-green-400",
        "dark:text-red-400",
      );
      if (macd.histogram > 0) {
        macdHist.classList.add("text-green-600", "dark:text-green-400");
      } else {
        macdHist.classList.add("text-red-600", "dark:text-red-400");
      }
    }
  }
  if (macdSignal && macd.histogram !== null) {
    removeSkeleton("tech-macd-signal");
    macdSignal.className =
      "text-sm font-bold px-3 py-1 rounded-full flex items-center justify-center";
    if (macd.histogram > 0) {
      macdSignal.textContent = "Tích cực";
      macdSignal.classList.add(
        "bg-green-100",
        "text-green-700",
        "dark:bg-green-500/20",
        "dark:text-green-400",
      );
    } else {
      macdSignal.textContent = "Tiêu cực";
      macdSignal.classList.add(
        "bg-red-100",
        "text-red-700",
        "dark:bg-red-500/20",
        "dark:text-red-400",
      );
    }
  }

  // ADX
  const adx = ind.adx || {};
  const adxVal = document.getElementById("tech-adx-val");
  const adxDmp = document.getElementById("tech-adx-dmp");
  const adxDmn = document.getElementById("tech-adx-dmn");
  const adxSignal = document.getElementById("tech-adx-signal");
  if (adxVal) {
    removeSkeleton("tech-adx-val");
    updateValueWithTooltip("tech-adx-val", formatNumber(adx.adx, 1));
  }
  if (adxDmp) {
    removeSkeleton("tech-adx-dmp");
    updateValueWithTooltip("tech-adx-dmp", formatNumber(adx.dmp, 1));
  }
  if (adxDmn) {
    removeSkeleton("tech-adx-dmn");
    updateValueWithTooltip("tech-adx-dmn", formatNumber(adx.dmn, 1));
  }
  if (adxSignal && adx.adx !== null) {
    removeSkeleton("tech-adx-signal");
    adxSignal.className =
      "text-sm font-bold px-3 py-1 rounded-full flex items-center justify-center";
    if (adx.adx > 25) {
      adxSignal.textContent = "Xu hướng mạnh";
      adxSignal.classList.add(
        "bg-blue-100",
        "text-blue-700",
        "dark:bg-blue-500/20",
        "dark:text-blue-400",
      );
    } else {
      adxSignal.textContent = "Đi ngang";
      adxSignal.classList.add(
        "bg-yellow-100",
        "text-yellow-700",
        "dark:bg-yellow-500/20",
        "dark:text-yellow-400",
      );
    }
  }

  // Moving Averages
  const maConfig = [
    { id: "tech-sma20", val: ind.sma20 },
    { id: "tech-sma50", val: ind.sma50 },
    { id: "tech-sma100", val: ind.sma100 },
    { id: "tech-sma200", val: ind.sma200 },
    { id: "tech-ema20", val: ind.ema20 },
    { id: "tech-ema50", val: ind.ema50 },
  ];
  maConfig.forEach((ma) => {
    if (ma.val !== undefined && ma.val !== null) {
      removeSkeleton(ma.id);
      updateValueWithTooltip(ma.id, formatPrice(ma.val));
    }
  });

  // Bollinger Bands
  const bb = ind.bollinger_bands || {};
  const bbUpper = document.getElementById("tech-bb-upper");
  const bbMiddle = document.getElementById("tech-bb-middle");
  const bbLower = document.getElementById("tech-bb-lower");
  const bbSignal = document.getElementById("tech-bb-signal");
  if (bbUpper) {
    removeSkeleton("tech-bb-upper");
    updateValueWithTooltip("tech-bb-upper", formatPrice(bb.upper));
  }
  if (bbMiddle) {
    removeSkeleton("tech-bb-middle");
    updateValueWithTooltip("tech-bb-middle", formatPrice(bb.middle));
  }
  if (bbLower) {
    removeSkeleton("tech-bb-lower");
    updateValueWithTooltip("tech-bb-lower", formatPrice(bb.lower));
  }
  if (bbSignal && ind.current_price && bb.upper && bb.lower) {
    bbSignal.className =
      "text-sm font-bold px-3 py-1 rounded-full flex items-center justify-center";
    if (ind.current_price > bb.upper) {
      bbSignal.textContent = "Quá mua";
      bbSignal.classList.add(
        "bg-red-100",
        "text-red-700",
        "dark:bg-red-500/20",
        "dark:text-red-400",
      );
    } else if (ind.current_price < bb.lower) {
      bbSignal.textContent = "Quá bán";
      bbSignal.classList.add(
        "bg-green-100",
        "text-green-700",
        "dark:bg-green-500/20",
        "dark:text-green-400",
      );
    } else {
      bbSignal.textContent = "Trong biên";
      bbSignal.classList.add(
        "bg-yellow-100",
        "text-yellow-700",
        "dark:bg-yellow-500/20",
        "dark:text-yellow-400",
      );
    }
  }

  // ATR
  if (ind.atr !== undefined) {
    removeSkeleton("tech-atr");
    updateValueWithTooltip("tech-atr", formatPrice(ind.atr));
  }

  // Volume Indicators
  const obvTrend = document.getElementById("tech-obv-trend");
  const cmf = document.getElementById("tech-cmf");
  const volSignal = document.getElementById("tech-vol-signal");
  if (obvTrend) {
    removeSkeleton("tech-obv-trend");
    const trend = ind.obv_trend;
    updateValueWithTooltip(
      "tech-obv-trend",
      trend === "increasing"
        ? "Tăng"
        : trend === "decreasing"
          ? "Giảm"
          : "Trung tính",
    );
    obvTrend.classList.remove(
      "text-green-600",
      "text-red-600",
      "dark:text-green-400",
      "dark:text-red-400",
    );
    if (trend === "increasing") {
      obvTrend.classList.add("text-green-600", "dark:text-green-400");
    } else if (trend === "decreasing") {
      obvTrend.classList.add("text-red-600", "dark:text-red-400");
    }
  }
  if (cmf) {
    removeSkeleton("tech-cmf");
    updateValueWithTooltip("tech-cmf", formatNumber(ind.cmf, 3));
  }
  if (volSignal && ind.obv_trend && ind.cmf !== null) {
    removeSkeleton("tech-vol-signal");
    volSignal.className =
      "text-sm font-bold px-3 py-1 rounded-full flex items-center justify-center";
    if (ind.obv_trend === "increasing" && ind.cmf > 0) {
      volSignal.textContent = "Dòng tiền vào";
      volSignal.classList.add(
        "bg-green-100",
        "text-green-700",
        "dark:bg-green-500/20",
        "dark:text-green-400",
      );
    } else if (ind.obv_trend === "decreasing" && ind.cmf < 0) {
      volSignal.textContent = "Dòng tiền ra";
      volSignal.classList.add(
        "bg-red-100",
        "text-red-700",
        "dark:bg-red-500/20",
        "dark:text-red-400",
      );
    } else {
      volSignal.textContent = "Trung tính";
      volSignal.classList.add(
        "bg-yellow-100",
        "text-yellow-700",
        "dark:bg-yellow-500/20",
        "dark:text-yellow-400",
      );
    }
  }

  // Pivot Points
  const pp = ind.pivot_points || {};
  const pivotIds = [
    "pivot",
    "pivot-r1",
    "pivot-r2",
    "pivot-r3",
    "pivot-s1",
    "pivot-s2",
    "pivot-s3",
  ];
  pivotIds.forEach((id) => removeSkeleton("tech-" + id));

  const pivot = document.getElementById("tech-pivot");
  const pivotR1 = document.getElementById("tech-pivot-r1");
  const pivotR2 = document.getElementById("tech-pivot-r2");
  const pivotR3 = document.getElementById("tech-pivot-r3");
  const pivotS1 = document.getElementById("tech-pivot-s1");
  const pivotS2 = document.getElementById("tech-pivot-s2");
  const pivotS3 = document.getElementById("tech-pivot-s3");
  if (pivot) {
    updateValueWithTooltip("tech-pivot", formatPrice(pp.pivot));
  }
  if (pivotR1) {
    updateValueWithTooltip("tech-pivot-r1", formatPrice(pp.r1));
  }
  if (pivotR2) {
    updateValueWithTooltip("tech-pivot-r2", formatPrice(pp.r2));
  }
  if (pivotR3) {
    updateValueWithTooltip("tech-pivot-r3", formatPrice(pp.r3));
  }
  if (pivotS1) {
    updateValueWithTooltip("tech-pivot-s1", formatPrice(pp.s1));
  }
  if (pivotS2) {
    updateValueWithTooltip("tech-pivot-s2", formatPrice(pp.s2));
  }
  if (pivotS3) {
    updateValueWithTooltip("tech-pivot-s3", formatPrice(pp.s3));
  }

  // Fibonacci Levels
  const fib = ind.fibonacci || {};
  const fibIds = [
    "fib-0",
    "fib-236",
    "fib-382",
    "fib-500",
    "fib-618",
    "fib-786",
    "fib-100",
  ];
  fibIds.forEach((id) => removeSkeleton("tech-" + id));

  const fib0 = document.getElementById("tech-fib-0");
  const fib236 = document.getElementById("tech-fib-236");
  const fib382 = document.getElementById("tech-fib-382");
  const fib500 = document.getElementById("tech-fib-500");
  const fib618 = document.getElementById("tech-fib-618");
  const fib786 = document.getElementById("tech-fib-786");
  const fib100 = document.getElementById("tech-fib-100");
  if (fib0) {
    updateValueWithTooltip("tech-fib-0", formatPrice(fib.level_0));
  }
  if (fib236) {
    updateValueWithTooltip("tech-fib-236", formatPrice(fib.level_236));
  }
  if (fib382) {
    updateValueWithTooltip("tech-fib-382", formatPrice(fib.level_382));
  }
  if (fib500) {
    updateValueWithTooltip("tech-fib-500", formatPrice(fib.level_500));
  }
  if (fib618) {
    updateValueWithTooltip("tech-fib-618", formatPrice(fib.level_618));
  }
  if (fib786) {
    updateValueWithTooltip("tech-fib-786", formatPrice(fib.level_786));
  }
  if (fib100) {
    updateValueWithTooltip("tech-fib-100", formatPrice(fib.level_100));
  }

  // Methods List
  const methodsList = document.getElementById("tech-methods-list");
  if (methodsList) {
    removeSkeleton("tech-methods-list");
    if (meth && meth.length > 0) {
      const template = /** @type {HTMLTemplateElement} */ (
        document.getElementById("analysis-method-item-template")
      );
      if (template) {
        const fragment = document.createDocumentFragment();
        meth.forEach((m) => {
          const clone = /** @type {HTMLElement} */ (
            template.content.cloneNode(true)
          ).firstElementChild;
          if (!clone) return;

          const signalColor =
            m.signal === "Bullish"
              ? "emerald"
              : m.signal === "Bearish"
                ? "rose"
                : "amber";
          const signalIcon =
            m.signal === "Bullish"
              ? "trending-up"
              : m.signal === "Bearish"
                ? "trending-down"
                : "minus";

          const nameEl = clone.querySelector(".method-name");
          if (nameEl) nameEl.textContent = m.name;

          const signalBadgeEl = clone.querySelector(".method-signal-badge");
          if (signalBadgeEl) {
            signalBadgeEl.classList.add(
              `bg-${signalColor}-100`,
              `dark:bg-${signalColor}-500/20`,
              `text-${signalColor}-700`,
              `dark:text-${signalColor}-400`,
            );
          }

          const iconEl = clone.querySelector(".method-icon");
          if (iconEl) iconEl.setAttribute("data-lucide", signalIcon);

          const signalTextEl = clone.querySelector(".method-signal-text");
          if (signalTextEl) signalTextEl.textContent = m.signal;

          const categoryEl = clone.querySelector(".method-category");
          if (categoryEl) categoryEl.textContent = m.category;

          const evaluationEl = clone.querySelector(".method-evaluation");
          if (evaluationEl) evaluationEl.textContent = m.evaluation;

          fragment.appendChild(clone);
        });
        methodsList.innerHTML = "";
        methodsList.appendChild(fragment);
      }
    }
    lucide.createIcons({ root: methodsList });
  }

  // Draw Sparklines
  if (rsiData.series) {
    drawSparkline(
      "tech-rsi-sparkline",
      rsiData.series,
      "rgba(99, 102, 241, 1)",
    );
  } else {
    removeSkeleton("tech-rsi-sparkline");
  }
  if (stoch.series) {
    drawSparkline(
      "tech-stoch-sparkline",
      stoch.series,
      "rgba(16, 185, 129, 1)",
    );
  } else {
    removeSkeleton("tech-stoch-sparkline");
  }
  if (macd.series) {
    drawSparkline("tech-macd-sparkline", macd.series, "rgba(139, 92, 246, 1)");
  } else {
    removeSkeleton("tech-macd-sparkline");
  }

  // Gauges
  const summary = gauges.summary || {};
  const gaugeSummary = document.getElementById("tech-gauge-summary");
  if (gaugeSummary) {
    removeSkeleton("tech-gauge-summary");
    gaugeSummary.querySelector(".gauge-text").textContent =
      summary.label || "--";
  }

  const gaugeMA = document.getElementById("tech-gauge-ma");
  if (gaugeMA) {
    removeSkeleton("tech-gauge-ma");
    gaugeMA.querySelector(".gauge-text").textContent =
      "MA: " + (gauges.movingAverage?.label || "--");
  }

  const gaugeOsc = document.getElementById("tech-gauge-osc");
  if (gaugeOsc) {
    removeSkeleton("tech-gauge-osc");
    gaugeOsc.querySelector(".gauge-text").textContent =
      "OSC: " + (gauges.oscillator?.label || "--");
  }

  // Chart
  if (ohlcv_data) {
    renderAnalysisChart(ohlcv_data);
  }
}

/**
 * Handle analysis summary event
 * @param {Object} summary - Summary data
 */
function handleAnalysisSummary(summary) {
  // Update short-term summary
  const shortTrend = document.getElementById("tech-short-trend");
  const shortSignal = document.getElementById("tech-short-signal");
  const shortConfidence = document.getElementById("tech-short-confidence");
  const shortConfidenceBar = document.getElementById(
    "tech-short-confidence-bar",
  );
  const shortTrendBadge = document.getElementById("tech-short-trend-badge");

  if (summary.short_term) {
    removeSkeleton("tech-short-trend");
    removeSkeleton("tech-short-signal");
    removeSkeleton("tech-short-confidence");
    removeSkeleton("tech-short-trend-badge");
    if (shortTrend) shortTrend.textContent = summary.short_term.trend || "--";
    if (shortSignal)
      shortSignal.textContent = summary.short_term.signal || "--";
    if (shortConfidence && summary.short_term.confidence) {
      const conf = (summary.short_term.confidence * 100).toFixed(0);
      shortConfidence.textContent = `${conf}%`;
    }
    if (shortConfidenceBar && summary.short_term.confidence) {
      const confPercent = summary.short_term.confidence * 100;
      const shortSkeleton = document.getElementById(
        "tech-short-confidence-skeleton",
      );
      if (shortSkeleton) shortSkeleton.remove();
      shortConfidenceBar.style.opacity = "1";
      shortConfidenceBar.style.left = `calc(${confPercent}% - 8px)`;
      const hue = (confPercent / 100) * 120;
      shortConfidenceBar.style.background = `linear-gradient(135deg, hsl(${hue}, 85%, 65%), hsl(${hue}, 80%, 45%))`;
      shortConfidenceBar.style.borderColor = `hsl(${hue}, 80%, 40%)`;
      shortConfidenceBar.style.boxShadow = `0 2px 8px hsla(${hue}, 80%, 50%, 0.6), 0 0 0 2px hsla(${hue}, 80%, 50%, 0.2)`;
    }
    if (shortTrendBadge) {
      shortTrendBadge.className =
        "text-xs font-bold px-2 py-1 rounded-full text-center";
      const sig = summary.short_term.signal?.toLowerCase() || "";
      if (sig.includes("mua")) {
        shortTrendBadge.textContent = "Mua";
        shortTrendBadge.classList.add(
          "bg-green-100",
          "text-green-700",
          "dark:bg-green-500/20",
          "dark:text-green-400",
        );
      } else if (sig.includes("bán") || sig.includes("phân phối")) {
        shortTrendBadge.textContent = "Bán";
        shortTrendBadge.classList.add(
          "bg-red-100",
          "text-red-700",
          "dark:bg-red-500/20",
          "dark:text-red-400",
        );
      } else {
        shortTrendBadge.textContent = summary.short_term.signal || "--";
        shortTrendBadge.classList.add(
          "bg-yellow-100",
          "text-yellow-700",
          "dark:bg-yellow-500/20",
          "dark:text-yellow-400",
        );
      }
    }
  }

  // Update long-term summary
  const longTrend = document.getElementById("tech-long-trend");
  const longSignal = document.getElementById("tech-long-signal");
  const longConfidence = document.getElementById("tech-long-confidence");
  const longConfidenceBar = document.getElementById("tech-long-confidence-bar");
  const longTrendBadge = document.getElementById("tech-long-trend-badge");

  if (summary.long_term) {
    removeSkeleton("tech-long-trend");
    removeSkeleton("tech-long-signal");
    removeSkeleton("tech-long-confidence");
    removeSkeleton("tech-long-trend-badge");
    if (longTrend) longTrend.textContent = summary.long_term.trend || "--";
    if (longSignal) longSignal.textContent = summary.long_term.signal || "--";
    if (longConfidence && summary.long_term.confidence) {
      const conf = (summary.long_term.confidence * 100).toFixed(0);
      longConfidence.textContent = `${conf}%`;
    }
    if (longConfidenceBar && summary.long_term.confidence) {
      const confPercent = summary.long_term.confidence * 100;
      const longSkeleton = document.getElementById(
        "tech-long-confidence-skeleton",
      );
      if (longSkeleton) longSkeleton.remove();
      longConfidenceBar.style.opacity = "1";
      longConfidenceBar.style.left = `calc(${confPercent}% - 8px)`;
      const hue = (confPercent / 100) * 120;
      longConfidenceBar.style.background = `linear-gradient(135deg, hsl(${hue}, 85%, 65%), hsl(${hue}, 80%, 45%))`;
      longConfidenceBar.style.borderColor = `hsl(${hue}, 80%, 40%)`;
      longConfidenceBar.style.boxShadow = `0 2px 8px hsla(${hue}, 80%, 50%, 0.6), 0 0 0 2px hsla(${hue}, 80%, 50%, 0.2)`;
    }
    if (longTrendBadge) {
      longTrendBadge.className =
        "text-xs font-bold px-2 py-1 rounded-full text-center";
      const sig = summary.long_term.signal?.toLowerCase() || "";
      if (sig.includes("tích lũy")) {
        longTrendBadge.textContent = "Tích lũy";
        longTrendBadge.classList.add(
          "bg-green-100",
          "text-green-700",
          "dark:bg-green-500/20",
          "dark:text-green-400",
        );
      } else if (sig.includes("phân phối")) {
        longTrendBadge.textContent = "Phân phối";
        longTrendBadge.classList.add(
          "bg-red-100",
          "text-red-700",
          "dark:bg-red-500/20",
          "dark:text-red-400",
        );
      } else {
        longTrendBadge.textContent = summary.long_term.signal || "--";
        longTrendBadge.classList.add(
          "bg-yellow-100",
          "text-yellow-700",
          "dark:bg-yellow-500/20",
          "dark:text-yellow-400",
        );
      }
    }
  }
}

/**
 * Clear technical analysis display (called when resetting stock selection)
 */
function clearAnalysisDisplay() {
  let template = /** @type {HTMLTemplateElement} */ (
    document.getElementById("analysis-content-timeframe-template")
  );

  if (template) {
    const clone = /** @type {DocumentFragment} */ (
      template.content.cloneNode(true)
    );
    const analysisContentTimeframeEl = document.getElementById(
      "analysis-content-timeframe",
    );
    if (analysisContentTimeframeEl) {
      analysisContentTimeframeEl.innerHTML = "";
      analysisContentTimeframeEl.appendChild(clone);
      lucide.createIcons({ root: analysisContentTimeframeEl });
    }
  }

  template = /** @type {HTMLTemplateElement} */ (
    document.getElementById("analysis-chart-collapsible-template")
  );

  if (template) {
    const clone = /** @type {DocumentFragment} */ (
      template.content.cloneNode(true)
    );
    const analysisChartCollapsibleEl = document.getElementById(
      "analysis-chart-collapsible",
    );
    if (analysisChartCollapsibleEl) {
      analysisChartCollapsibleEl.innerHTML = "";
      analysisChartCollapsibleEl.appendChild(clone);
      lucide.createIcons({ root: analysisChartCollapsibleEl });
    }
  }

  template = /** @type {HTMLTemplateElement} */ (
    document.getElementById("analysis-tab-content-container-template")
  );

  if (template) {
    const clone = /** @type {DocumentFragment} */ (
      template.content.cloneNode(true)
    );
    const analysisTabContentContainerEl = document.getElementById(
      "analysis-tab-content-container",
    );
    if (analysisTabContentContainerEl) {
      analysisTabContentContainerEl.innerHTML = "";
      analysisTabContentContainerEl.appendChild(clone);
      lucide.createIcons({ root: analysisTabContentContainerEl });
    }
  }

  // Show chart's skeleton
  const chartContainer = document.getElementById("analysis-candlestick-chart");
  if (chartContainer) {
    const template = /** @type {HTMLTemplateElement} */ (
      document.getElementById("analysis-chart-skeleton-template")
    );
    if (template) {
      const clone = /** @type {DocumentFragment} */ (
        template.content.cloneNode(true)
      );
      const barsContainer = clone.querySelector(".chart-skeleton-bars");
      if (barsContainer) {
        for (let i = 0; i < 20; i++) {
          const bar = document.createElement("div");
          bar.className =
            "flex-1 inset-0 bg-slate-200/50 dark:bg-slate-800/40 skeleton-shimmer rounded";
          bar.style.height = `${30 + Math.random() * 60}%`;
          barsContainer.appendChild(bar);
        }
      }
      chartContainer.append(clone.children[0]);
    }
  }

  initAnalysisChartResizer();
}
