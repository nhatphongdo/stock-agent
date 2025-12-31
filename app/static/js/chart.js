// Chart Module - Global chart instances for cleanup (Lightweight Charts)
let priceChart = null;
let volumeChart = null;
let candleSeries = null;
let volumeSeries = null;
let indicatorSeries = []; // Array to hold indicator line series
let indicatorValues = {}; // Store raw indicator values mapping time -> {key: value}
let currentChartSymbol = null;

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

// Render both charts (async - fetches real data from API)
async function renderAdvancedChart(symbol, timeframe, interval) {
  const candleCanvas = document.getElementById("candlestick-chart");
  const volumeCanvas = document.getElementById("volume-chart");
  if (!candleCanvas || !volumeCanvas) return;

  // Destroy previous instances
  if (priceChart) {
    priceChart.remove();
    priceChart = null;
  }
  if (volumeChart) {
    volumeChart.remove();
    volumeChart = null;
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

  const skeletonHTML = `
    <div class="h-full w-full flex flex-col gap-2 p-2 chart-skeleton">
      <div class="flex-1 flex items-end gap-1">
        ${Array(20)
          .fill(0)
          .map(
            () =>
              `<div class="flex-1 skeleton-shimmer rounded" style="height: ${
                30 + Math.random() * 60
              }%"></div>`,
          )
          .join("")}
      </div>
      <div class="h-2 skeleton-shimmer rounded w-full"></div>
    </div>
  `;

  // Stable container management: don't nuke parents, just toggle contents
  const candleParent = candleCanvas.parentElement;
  const volumeParent = volumeCanvas.parentElement;

  if (candleParent) {
    candleParent
      .querySelectorAll(".chart-skeleton")
      .forEach((el) => el.remove());
    candleCanvas.classList.add("hidden");
    candleCanvas.insertAdjacentHTML("beforebegin", skeletonHTML);
  }
  if (volumeParent) {
    volumeParent
      .querySelectorAll(".chart-skeleton")
      .forEach((el) => el.remove());
    volumeCanvas.classList.add("hidden");
    volumeCanvas.insertAdjacentHTML("beforebegin", skeletonHTML);
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
    const candleParent =
      document.getElementById("candlestick-chart")?.parentElement;
    const volumeParent = document.getElementById("volume-chart")?.parentElement;
    const stockInfo = getStockInfo(symbol);
    const exchange = stockInfo?.exchange || "HOSE";
    const errorTemplate = /** @type {HTMLTemplateElement | null} */ (
      document.getElementById("chart-error-template")
    );
    if (errorTemplate && candleParent) {
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
      candleParent.innerHTML = "";
      candleParent.appendChild(errorContent);
    }
    if (volumeParent) volumeParent.innerHTML = "";
    lucide.createIcons();
    return; // Exit early, don't try to render chart
  }

  // Show chart containers, remove skeletons
  const candleParentUpdate =
    document.getElementById("candlestick-chart")?.parentElement;
  const volumeParentUpdate =
    document.getElementById("volume-chart")?.parentElement;
  if (candleParentUpdate) {
    candleParentUpdate
      .querySelectorAll(".chart-skeleton")
      .forEach((el) => el.remove());
    document.getElementById("candlestick-chart")?.classList.remove("hidden");
  }
  if (volumeParentUpdate) {
    volumeParentUpdate
      .querySelectorAll(".chart-skeleton")
      .forEach((el) => el.remove());
    document.getElementById("volume-chart")?.classList.remove("hidden");
  }

  const isDark = document.documentElement.classList.contains("dark");

  // Full theme presets for Lightweight Charts
  const darkTheme = {
    layout: {
      background: { type: "solid", color: "#0f172a" },
      textColor: "#94a3b8",
    },
    grid: {
      vertLines: { color: "rgba(148, 163, 184, 0.1)" },
      horzLines: { color: "rgba(148, 163, 184, 0.1)" },
    },
    rightPriceScale: {
      borderColor: "rgba(148, 163, 184, 0.2)",
    },
    timeScale: {
      borderColor: "rgba(148, 163, 184, 0.2)",
    },
    crosshair: {
      mode: LightweightCharts.CrosshairMode.Normal,
      vertLine: {
        color: "rgba(148, 163, 184, 0.5)",
        width: 1,
        style: LightweightCharts.LineStyle.Dashed,
        labelBackgroundColor: "#334155",
      },
      horzLine: {
        color: "rgba(148, 163, 184, 0.5)",
        width: 1,
        style: LightweightCharts.LineStyle.Dashed,
        labelBackgroundColor: "#334155",
      },
    },
  };

  const lightTheme = {
    layout: {
      background: { type: "solid", color: "#ffffff" },
      textColor: "#334155",
    },
    grid: {
      vertLines: { color: "rgba(100, 116, 139, 0.1)" },
      horzLines: { color: "rgba(100, 116, 139, 0.1)" },
    },
    rightPriceScale: {
      borderColor: "rgba(100, 116, 139, 0.2)",
    },
    timeScale: {
      borderColor: "rgba(100, 116, 139, 0.2)",
    },
    crosshair: {
      mode: LightweightCharts.CrosshairMode.Normal,
      vertLine: {
        color: "rgba(100, 116, 139, 0.5)",
        width: 1,
        style: LightweightCharts.LineStyle.Dashed,
        labelBackgroundColor: "#f1f5f9",
      },
      horzLine: {
        color: "rgba(100, 116, 139, 0.5)",
        width: 1,
        style: LightweightCharts.LineStyle.Dashed,
        labelBackgroundColor: "#f1f5f9",
      },
    },
  };

  const theme = isDark ? darkTheme : lightTheme;

  // Get chart containers
  const priceContainer = document.getElementById("candlestick-chart");
  const volumeContainer = document.getElementById("volume-chart");
  if (!priceContainer || !volumeContainer) return;

  // Create Price Chart with theme
  priceChart = LightweightCharts.createChart(priceContainer, {
    autoSize: true,
    ...theme,
    timeScale: {
      ...theme.timeScale,
      timeVisible: apiInterval.includes("m") || apiInterval === "1H",
      secondsVisible: false,
    },
  });

  // Create Volume Chart with theme
  volumeChart = LightweightCharts.createChart(volumeContainer, {
    autoSize: true,
    ...theme,
    timeScale: {
      ...theme.timeScale,
      timeVisible: false,
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
  candleSeries = priceChart.addCandlestickSeries({
    upColor: CONFIG.COLORS.UP,
    downColor: CONFIG.COLORS.DOWN,
    borderUpColor: CONFIG.COLORS.UP,
    borderDownColor: CONFIG.COLORS.DOWN,
    wickUpColor: CONFIG.COLORS.UP,
    wickDownColor: CONFIG.COLORS.DOWN,
  });
  candleSeries.setData(chartData);

  // Add Volume Series (Histogram)
  volumeSeries = volumeChart.addHistogramSeries({
    priceFormat: { type: "volume" },
    priceScaleId: "right",
  });
  volumeSeries.setData(volumeData);

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
    const maSeries = priceChart.addLineSeries({
      color: "#3b82f6",
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    });
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
    const emaSeries = priceChart.addLineSeries({
      color: "#f97316",
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    });
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

    const upperSeries = priceChart.addLineSeries({
      color: "#a855f7",
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    upperSeries.setData(upperData);
    indicatorSeries.push(upperSeries);

    const lowerSeries = priceChart.addLineSeries({
      color: "#a855f7",
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      priceLineVisible: false,
      lastValueVisible: false,
    });
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
    const rsiSeries = priceChart.addLineSeries({
      color: CONFIG.COLORS.RSI,
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dotted,
      priceLineVisible: false,
      lastValueVisible: false,
    });
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

    const macdSeries = priceChart.addLineSeries({
      color: CONFIG.COLORS.MACD_LINE,
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    macdSeries.setData(macdData);
    indicatorSeries.push(macdSeries);

    const signalSeries = priceChart.addLineSeries({
      color: CONFIG.COLORS.MACD_SIGNAL,
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      priceLineVisible: false,
      lastValueVisible: false,
    });
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
    const volSmaSeries = volumeChart.addLineSeries({
      color: CONFIG.COLORS.VOLUME_SMA,
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    volSmaSeries.setData(volSmaData);
    indicatorSeries.push(volSmaSeries);
    // Store for tooltip
    volSmaData.forEach((d) => {
      if (!indicatorValues[d.time]) indicatorValues[d.time] = {};
      indicatorValues[d.time].volSma = d.value;
    });
  }

  // Synchronize time scales between price and volume charts
  priceChart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
    if (range !== null) {
      volumeChart.timeScale().setVisibleLogicalRange(range);
    }
  });
  volumeChart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
    if (range !== null) {
      priceChart.timeScale().setVisibleLogicalRange(range);
    }
  });

  // Create tooltip elements for both charts (follows crosshair)
  const createTooltip = (container) => {
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
    container.style.position = "relative";
    container.appendChild(tooltip);
    return tooltip;
  };

  const priceTooltip = createTooltip(priceContainer);
  const volumeTooltip = createTooltip(volumeContainer);

  // Helper function to format full datetime
  const formatFullDateTime = (timestamp) => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleString("vi-VN", {
      weekday: "long",
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Helper function to format price with thousands separator
  const formatPrice = (price) => {
    return price.toLocaleString("vi-VN", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    });
  };

  // Helper function to format volume with thousands separator
  const formatVolume = (vol) => {
    return vol.toLocaleString("vi-VN");
  };

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
        }; opacity: 0.8;">RSI(14):</span> <strong>${values.rsi.toFixed(
          2,
        )}</strong></div>`;
        count++;
      }
      if (values.macdLine !== undefined) {
        html += `<div><span style="color: ${
          CONFIG.COLORS.MACD_LINE
        }; opacity: 0.8;">MACD:</span> <strong>${values.macdLine.toFixed(
          2,
        )}</strong></div>`;
        html += `<div><span style="color: ${
          CONFIG.COLORS.MACD_SIGNAL
        }; opacity: 0.8;">Signal:</span> <strong>${values.macdSignal.toFixed(
          2,
        )}</strong></div>`;
        count++;
      }
    } else {
      if (values.volSma !== undefined) {
        html += `<div><span style="color: ${
          CONFIG.COLORS.VOLUME_SMA
        }; opacity: 0.8;">Vol SMA(20):</span> <strong>${formatVolume(
          values.volSma,
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

  // Crosshair sync with moving tooltips
  priceChart.subscribeCrosshairMove((param) => {
    if (param.time && param.point) {
      // Sync crosshair with volume chart
      volumeChart.setCrosshairPosition(
        volumeSeries.dataByIndex(param.logical),
        param.time,
        volumeSeries,
      );

      // Update price tooltip with OHLC
      const candlePrice = /** @type {ICandleData | undefined} */ (
        param.seriesData.get(candleSeries)
      );
      if (candlePrice) {
        const changePercent = (
          ((candlePrice.close - candlePrice.open) / candlePrice.open) *
          100
        ).toFixed(2);
        const changeColor =
          candlePrice.close >= candlePrice.open ? "#10b981" : "#ef4444";
        const changeSign = candlePrice.close >= candlePrice.open ? "+" : "";
        priceTooltip.innerHTML = `
          <div style="margin-bottom: 6px; font-weight: 500; opacity: 0.8;">${formatFullDateTime(
            param.time,
          )}</div>
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
          ${renderTooltipIndicators(param.time)}
        `;
        priceTooltip.style.display = "block";
        updateTooltipPosition(priceTooltip, priceContainer, param);
      }

      // Update volume tooltip
      const volData = /** @type {IVolumeData | undefined} */ (
        param.seriesData.get(volumeSeries)
      );
      if (volData) {
        volumeTooltip.innerHTML = `
          <div style="margin-bottom: 6px; font-weight: 500; opacity: 0.8;">${formatFullDateTime(
            param.time,
          )}</div>
          <div><span style="opacity: 0.6;">Volume:</span> <strong>${formatVolume(
            volData.value,
          )}</strong></div>
          ${renderTooltipIndicators(param.time, true)}
        `;
        volumeTooltip.style.display = "block";
        updateTooltipPosition(volumeTooltip, volumeContainer, param);
      }
    } else {
      priceTooltip.style.display = "none";
      volumeTooltip.style.display = "none";
    }
  });

  volumeChart.subscribeCrosshairMove((param) => {
    if (param.time && param.point) {
      // Sync crosshair with price chart
      priceChart.setCrosshairPosition(
        candleSeries.dataByIndex(param.logical),
        param.time,
        candleSeries,
      );

      // Update volume tooltip
      const volData = /** @type {IVolumeData | undefined} */ (
        param.seriesData.get(volumeSeries)
      );
      if (volData) {
        volumeTooltip.innerHTML = `
          <div style="margin-bottom: 6px; font-weight: 500; opacity: 0.8;">${formatFullDateTime(
            param.time,
          )}</div>
          <div><span style="opacity: 0.6;">Volume:</span> <strong>${formatVolume(
            volData.value,
          )}</strong></div>
          ${renderTooltipIndicators(param.time, true)}
        `;
        volumeTooltip.style.display = "block";
        updateTooltipPosition(volumeTooltip, volumeContainer, param);
      }

      // Update price tooltip from synced data
      const candlePrice = /** @type {ICandleData | undefined} */ (
        candleSeries.dataByIndex(param.logical)
      );
      if (candlePrice) {
        const changePercent = (
          ((candlePrice.close - candlePrice.open) / candlePrice.open) *
          100
        ).toFixed(2);
        const changeColor =
          candlePrice.close >= candlePrice.open ? "#10b981" : "#ef4444";
        const changeSign = candlePrice.close >= candlePrice.open ? "+" : "";
        priceTooltip.innerHTML = `
          <div style="margin-bottom: 6px; font-weight: 500; opacity: 0.8;">${formatFullDateTime(
            param.time,
          )}</div>
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
          ${renderTooltipIndicators(param.time)}
        `;
        priceTooltip.style.display = "block";
      }
    } else {
      priceTooltip.style.display = "none";
      volumeTooltip.style.display = "none";
    }
  });

  setTimeout(() => {
    window.dispatchEvent(new Event("resize"));
    if (typeof priceChart !== "undefined" && priceChart)
      priceChart.timeScale().fitContent();
    if (typeof volumeChart !== "undefined" && volumeChart)
      volumeChart.timeScale().fitContent();
  }, 50);
}
