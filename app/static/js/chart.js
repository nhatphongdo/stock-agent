// Chart Module - Global chart instances for cleanup (Lightweight Charts)
let priceChart = null;
let candleSeries = null;
let volumeSeries = null;
let indicatorSeries = []; // Array to hold indicator line series
let indicatorValues = {}; // Store raw indicator values mapping time -> {key: value}
let currentChartSymbol = null;

// Refresh charts by fitting content to time scale
function refreshCharts() {
  if (typeof priceChart !== "undefined" && priceChart) {
    const isDark = document.documentElement.classList.contains("dark");
    const theme = isDark ? CONFIG.CHART_THEMES.dark : CONFIG.CHART_THEMES.light;
    priceChart.applyOptions(theme);
    priceChart.timeScale().fitContent();
  }
}

// Calculate Moving Average
function calculateMA(data, period) {
  return data.map((_, i, arr) => {
    if (i < period - 1) return null;
    const slice = arr.slice(i - period + 1, i + 1);
    return slice.reduce((sum, d) => sum + d.c, 0) / period;
  });
}

// Calculate EMA
function calculateEMA(data, period) {
  const k = 2 / (period + 1);
  const ema = [data[0].c];
  for (let i = 1; i < data.length; i++) {
    ema.push(data[i].c * k + ema[i - 1] * (1 - k));
  }
  return ema;
}

// Calculate Bollinger Bands
function calculateBB(data, period = 20, stdDev = 2) {
  const ma = calculateMA(data, period);
  return ma.map((mean, i) => {
    if (mean === null) return { upper: null, middle: null, lower: null };
    const slice = data.slice(Math.max(0, i - period + 1), i + 1);
    const variance =
      slice.reduce((sum, d) => sum + Math.pow(d.c - mean, 2), 0) / period;
    const std = Math.sqrt(variance);
    return {
      upper: mean + stdDev * std,
      middle: mean,
      lower: mean - stdDev * std,
    };
  });
}

// Calculate RSI (Relative Strength Index)
function calculateRSI(data, period = 14) {
  const changes = data.map((d, i) => (i === 0 ? 0 : d.c - data[i - 1].c));
  const gains = changes.map((c) => (c > 0 ? c : 0));
  const losses = changes.map((c) => (c < 0 ? -c : 0));

  let avgGain = gains.slice(1, period + 1).reduce((a, b) => a + b, 0) / period;
  let avgLoss = losses.slice(1, period + 1).reduce((a, b) => a + b, 0) / period;

  return data.map((_, i) => {
    if (i < period) return null;
    if (i === period) {
      return avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
    }
    avgGain = (avgGain * (period - 1) + gains[i]) / period;
    avgLoss = (avgLoss * (period - 1) + losses[i]) / period;
    return avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
  });
}

// Calculate MACD (Moving Average Convergence Divergence)
function calculateMACD(data, fast = 12, slow = 26, signal = 9) {
  const emaFast = calculateEMA(data, fast);
  const emaSlow = calculateEMA(data, slow);
  const macdLine = emaFast.map((f, i) =>
    i < slow - 1 ? null : f - emaSlow[i],
  );

  // Calculate signal line (EMA of MACD line)
  const validMacd = macdLine.filter((v) => v !== null);
  const k = 2 / (signal + 1);
  const signalLine = [];
  let signalEma = validMacd[0];

  let validIndex = 0;
  for (let i = 0; i < macdLine.length; i++) {
    if (macdLine[i] === null) {
      signalLine.push(null);
    } else {
      if (validIndex === 0) {
        signalLine.push(signalEma);
      } else if (validIndex < signal) {
        signalEma = (macdLine[i] + signalEma * validIndex) / (validIndex + 1);
        signalLine.push(null);
      } else {
        signalEma = macdLine[i] * k + signalEma * (1 - k);
        signalLine.push(signalEma);
      }
      validIndex++;
    }
  }

  const histogram = macdLine.map((m, i) =>
    m === null || signalLine[i] === null ? null : m - signalLine[i],
  );

  return { macdLine, signalLine, histogram };
}

// Calculate Volume SMA
function calculateVolumeSMA(data, period = 20) {
  return data.map((_, i, arr) => {
    if (i < period - 1) return null;
    const slice = arr.slice(i - period + 1, i + 1);
    return slice.reduce((sum, d) => sum + d.v, 0) / period;
  });
}

// Trigger chart display and initialization
function triggerChartDisplay(symbol) {
  document.getElementById("chart-tab-content-empty").classList.add("hidden");
  document
    .getElementById("chart-tab-content-container")
    .classList.remove("hidden");
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
  [
    "indicator-ma",
    "indicator-ema",
    "indicator-bb",
    "indicator-rsi",
    "indicator-macd",
    "indicator-vol-sma",
  ].forEach((id) => {
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

  // Add Indicators
  const showMA = /** @type {HTMLInputElement | null} */ (
    document.getElementById("indicator-ma")
  )?.checked;
  const showEMA = /** @type {HTMLInputElement | null} */ (
    document.getElementById("indicator-ema")
  )?.checked;
  const showBB = /** @type {HTMLInputElement | null} */ (
    document.getElementById("indicator-bb")
  )?.checked;
  const showRSI = /** @type {HTMLInputElement | null} */ (
    document.getElementById("indicator-rsi")
  )?.checked;
  const showMACD = /** @type {HTMLInputElement | null} */ (
    document.getElementById("indicator-macd")
  )?.checked;
  const showVolSMA = /** @type {HTMLInputElement | null} */ (
    document.getElementById("indicator-vol-sma")
  )?.checked;

  if (showMA) {
    const maData = calculateMA(data, 20)
      .map((v, i) => ({
        time: Math.floor(data[i].x.getTime() / 1000),
        value: v,
      }))
      .filter((d) => d.value !== null);
    const maSeries = priceChart.addSeries(
      LightweightCharts.LineSeries,
      {
        color: "#3b82f6",
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: false,
      },
      0,
    );
    maSeries.setData(maData);
    indicatorSeries.push(maSeries);
    // Store for tooltip
    maData.forEach((d) => {
      if (!indicatorValues[d.time]) indicatorValues[d.time] = {};
      indicatorValues[d.time].ma = d.value;
    });
  }

  if (showEMA) {
    const emaData = calculateEMA(data, 9)
      .map((v, i) => ({
        time: Math.floor(data[i].x.getTime() / 1000),
        value: v,
      }))
      .filter((d) => d.value !== null);
    const emaSeries = priceChart.addSeries(
      LightweightCharts.LineSeries,
      {
        color: "#f97316",
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: false,
      },
      0,
    );
    emaSeries.setData(emaData);
    indicatorSeries.push(emaSeries);
    // Store for tooltip
    emaData.forEach((d) => {
      if (!indicatorValues[d.time]) indicatorValues[d.time] = {};
      indicatorValues[d.time].ema = d.value;
    });
  }

  if (showBB) {
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

    const upperSeries = priceChart.addSeries(
      LightweightCharts.LineSeries,
      {
        color: "#a855f7",
        lineWidth: 1,
        lineStyle: LightweightCharts.LineStyle.Dashed,
        priceLineVisible: false,
        lastValueVisible: false,
      },
      0,
    );
    upperSeries.setData(upperData);
    indicatorSeries.push(upperSeries);

    const lowerSeries = priceChart.addSeries(
      LightweightCharts.LineSeries,
      {
        color: "#a855f7",
        lineWidth: 1,
        lineStyle: LightweightCharts.LineStyle.Dashed,
        priceLineVisible: false,
        lastValueVisible: false,
      },
      0,
    );
    lowerSeries.setData(lowerData);
    indicatorSeries.push(lowerSeries);
    // Store for tooltip
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

  if (showRSI) {
    const rsi = calculateRSI(data, 14);
    const prices = data.map((d) => d.c);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const rsiData = rsi
      .map((v, i) => ({
        time: Math.floor(data[i].x.getTime() / 1000),
        value: v === null ? null : minPrice + (v / 100) * (maxPrice - minPrice),
      }))
      .filter((d) => d.value !== null);
    const rsiSeries = priceChart.addSeries(
      LightweightCharts.LineSeries,
      {
        color: CONFIG.COLORS.RSI,
        lineWidth: 1,
        lineStyle: LightweightCharts.LineStyle.Dotted,
        priceLineVisible: false,
        lastValueVisible: false,
      },
      0,
    );
    rsiSeries.setData(rsiData);
    indicatorSeries.push(rsiSeries);
    // Store raw RSI values for tooltip
    rsi.forEach((v, i) => {
      if (v !== null) {
        const time = Math.floor(data[i].x.getTime() / 1000);
        if (!indicatorValues[time]) indicatorValues[time] = {};
        indicatorValues[time].rsi = v;
      }
    });
  }

  if (showMACD) {
    const macd = calculateMACD(data, 12, 26, 9);
    const prices = data.map((d) => d.c);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const priceRange = maxPrice - minPrice;
    const macdValues = macd.macdLine.filter((v) => v !== null);
    const macdMax = Math.max(...macdValues.map(Math.abs)) || 1;
    const scaleMACD = (v) =>
      v === null
        ? null
        : (maxPrice + minPrice) / 2 + (v / macdMax) * (priceRange / 4);

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

    const macdSeries = priceChart.addSeries(
      LightweightCharts.LineSeries,
      {
        color: CONFIG.COLORS.MACD_LINE,
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: false,
      },
      0,
    );
    macdSeries.setData(macdData);
    indicatorSeries.push(macdSeries);

    const signalSeries = priceChart.addSeries(
      LightweightCharts.LineSeries,
      {
        color: CONFIG.COLORS.MACD_SIGNAL,
        lineWidth: 1,
        lineStyle: LightweightCharts.LineStyle.Dashed,
        priceLineVisible: false,
        lastValueVisible: false,
      },
      0,
    );
    signalSeries.setData(signalData);
    indicatorSeries.push(signalSeries);
    // Store raw MACD values for tooltip
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

  if (showVolSMA) {
    const volSmaData = calculateVolumeSMA(data, 20)
      .map((v, i) => ({
        time: Math.floor(data[i].x.getTime() / 1000),
        value: v,
      }))
      .filter((d) => d.value !== null);

    // Add to pane 1 (volume pane)
    const volSmaSeries = priceChart.addSeries(
      LightweightCharts.LineSeries,
      {
        color: CONFIG.COLORS.VOLUME_SMA,
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: false,
      },
      1,
    );
    volSmaSeries.setData(volSmaData);
    indicatorSeries.push(volSmaSeries);
    // Store for tooltip
    volSmaData.forEach((d) => {
      if (!indicatorValues[d.time]) indicatorValues[d.time] = {};
      indicatorValues[d.time].volSma = d.value;
    });
  }

  // Create tooltip element for the chart (follows crosshair)
  const createTooltip = (targetContainer) => {
    const tooltip = document.createElement("div");
    tooltip.style.cssText = `
      position: absolute;
      z-index: 100;
      font-size: 12px;
      font-family: sans-serif;
      line-height: 1.5;
      padding: 10px 14px;
      border-radius: 8px;
      pointer-events: none;
      display: none;
      white-space: nowrap;
      ${
        isDark
          ? "background: rgba(30, 41, 59, 0.95); color: #e2e8f0; border: 1px solid rgba(148, 163, 184, 0.2);"
          : "background: rgba(255, 255, 255, 0.95); color: #1e293b; border: 1px solid rgba(100, 116, 139, 0.2);"
      }
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    targetContainer.style.position = "relative";
    targetContainer.appendChild(tooltip);
    return tooltip;
  };

  const chartTooltip = createTooltip(chartContainer);

  // Helper for indicator values in tooltip
  const renderTooltipIndicators = (time, isVolumeChart = false) => {
    const values = indicatorValues[time];
    if (!values) return "";
    let html =
      '<div style="margin-top: 6px; border-top: 1px solid rgba(148, 163, 184, 0.2); padding-top: 4px;">';
    let count = 0;

    if (!isVolumeChart) {
      if (values.ma !== undefined) {
        html += `<div><span style="color: #3b82f6; opacity: 0.8;">MA(20):</span> <strong>${formatPrice(
          values.ma,
        )}</strong></div>`;
        count++;
      }
      if (values.ema !== undefined) {
        html += `<div><span style="color: #f97316; opacity: 0.8;">EMA(9):</span> <strong>${formatPrice(
          values.ema,
        )}</strong></div>`;
        count++;
      }
      if (values.bbUpper !== undefined) {
        html += `<div><span style="color: #a855f7; opacity: 0.8;">BB Upper:</span> <strong>${formatPrice(
          values.bbUpper,
        )}</strong></div>`;
        html += `<div><span style="color: #a855f7; opacity: 0.8;">BB Lower:</span> <strong>${formatPrice(
          values.bbLower,
        )}</strong></div>`;
        count++;
      }
      if (values.rsi !== undefined) {
        html += `<div><span style="color: ${
          CONFIG.COLORS.RSI
        }; opacity: 0.8;">RSI(14):</span> <strong>${formatNumber(
          values.rsi,
          2,
        )}</strong></div>`;
        count++;
      }
      if (values.macdLine !== undefined) {
        html += `<div><span style="color: ${
          CONFIG.COLORS.MACD_LINE
        }; opacity: 0.8;">MACD:</span> <strong>${formatNumber(
          values.macdLine,
          2,
        )}</strong></div>`;
        html += `<div><span style="color: ${
          CONFIG.COLORS.MACD_SIGNAL
        }; opacity: 0.8;">Signal:</span> <strong>${formatNumber(
          values.macdSignal,
          2,
        )}</strong></div>`;
        count++;
      }
    } else {
      if (values.volSma !== undefined) {
        html += `<div><span style="color: ${
          CONFIG.COLORS.VOLUME_SMA
        }; opacity: 0.8;">Vol SMA(20):</span> <strong>${formatNumber(
          values.volSma,
          2,
        )}</strong></div>`;
        count++;
      }
    }

    html += "</div>";
    return count > 0 ? html : "";
  };

  // Update tooltip position to follow crosshair
  const updateTooltipPosition = (tooltip, container, param) => {
    if (!param.point) return;

    const containerRect = container.getBoundingClientRect();
    const tooltipWidth = tooltip.offsetWidth || 200;
    const tooltipHeight = tooltip.offsetHeight || 100;

    let left = param.point.x + 15;
    let top = param.point.y + 15;

    // Keep tooltip within container bounds
    if (left + tooltipWidth > containerRect.width) {
      left = param.point.x - tooltipWidth - 15;
    }
    if (top + tooltipHeight > containerRect.height) {
      top = param.point.y - tooltipHeight - 15;
    }
    if (left < 0) left = 10;
    if (top < 0) top = 10;

    tooltip.style.left = left + "px";
    tooltip.style.top = top + "px";
  };

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

      // Add indicator values
      tooltipContent += renderTooltipIndicators(param.time);

      // Add volume SMA if exists
      const volIndicators = renderTooltipIndicators(param.time, true);
      if (volIndicators) {
        tooltipContent += volIndicators;
      }

      chartTooltip.innerHTML = tooltipContent;
      chartTooltip.style.display = "block";
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
