/**
 * Chart Utilities - Shared tooltip and chart helper functions
 */

/**
 * Shared Indicator Configuration with colors, labels, and pane info
 * This is the single source of truth for indicator display properties
 */
const SHARED_INDICATOR_CONFIG = {
  // Moving Averages (overlay on price, pane 0)
  ma: { label: "SMA(20)", color: "#3b82f6", pane: 0 },
  ema: { label: "EMA(9)", color: "#f97316", pane: 0 },
  wma: { label: "WMA(20)", color: "#06b6d4", pane: 0 },
  vwap: { label: "VWAP", color: "#8b5cf6", pane: 0 },
  // Bands/Channels
  bb: { label: "BB", color: "#a855f7", pane: 0 },
  atr: { label: "ATR(14)", color: "#ec4899", pane: 0 },
  // Oscillators
  rsi: { label: "RSI(14)", color: "#f59e0b", pane: 0 },
  macd: {
    label: "MACD",
    colors: { line: "#3b82f6", signal: "#ef4444" },
    pane: 0,
  },
  stoch: { label: "Stoch", colors: { k: "#10b981", d: "#ef4444" }, pane: 0 },
  williams: { label: "Will %R", color: "#06b6d4", pane: 0 },
  cci: { label: "CCI(20)", color: "#8b5cf6", pane: 0 },
  roc: { label: "ROC(10)", color: "#f97316", pane: 0 },
  // Trend
  adx: {
    label: "ADX(14)",
    colors: { adx: "#22c55e", plusDI: "#3b82f6", minusDI: "#ef4444" },
    pane: 0,
  },
  // Volume (in volume pane, pane 1)
  volSma: { label: "Vol SMA(20)", color: "#8b5cf6", pane: 1 },
  obv: { label: "OBV", color: "#06b6d4", pane: 1 },
  mfi: { label: "MFI(14)", color: "#f59e0b", pane: 1 },
  cmf: { label: "CMF(20)", color: "#ec4899", pane: 1 },
  // Support/Resistance
  pivot: {
    label: "Pivot S/R",
    colors: { resistance: "#ef4444", support: "#10b981", pivot: "#6366f1" },
    pane: 0,
  },
  fib: {
    label: "Fibonacci",
    colors: { level: "#f59e0b", key: "#8b5cf6" },
    pane: 0,
  },
};

// Common line series options - reduces repetition
const LINE_SERIES_DEFAULTS = {
  lineWidth: 1,
  priceLineVisible: false,
  lastValueVisible: false,
};

// Mapping from indicator key to HTML element ID suffix (for kebab-case IDs)
const INDICATOR_KEY_TO_ID_SUFFIX = {
  ma: "ma",
  ema: "ema",
  wma: "wma",
  vwap: "vwap",
  bb: "bb",
  atr: "atr",
  rsi: "rsi",
  macd: "macd",
  stoch: "stoch",
  williams: "williams",
  cci: "cci",
  roc: "roc",
  adx: "adx",
  volSma: "vol-sma",
  obv: "obv",
  mfi: "mfi",
  cmf: "cmf",
  pivot: "pivot",
  fib: "fib",
};

/**
 * Generate indicator ID-to-key mapping for a given prefix
 * @param {string} prefix - Prefix for the indicator IDs (e.g., "" for chart.js, "analysis" for analysis.js)
 * @returns {Object} - Mapping from ID to config key
 */
function generateIndicatorIdToKey(prefix = "") {
  const result = {};
  for (const key of Object.keys(SHARED_INDICATOR_CONFIG)) {
    const suffix = INDICATOR_KEY_TO_ID_SUFFIX[key] || key;
    const id = prefix ? `${prefix}-indicator-${suffix}` : `indicator-${suffix}`;
    result[id] = key;
  }
  return result;
}

/**
 * Get all indicator IDs for a given prefix
 * @param {string} prefix - Prefix for the indicator IDs
 * @returns {string[]} - Array of all indicator checkbox IDs
 */
function getAllIndicatorIds(prefix = "") {
  return Object.keys(generateIndicatorIdToKey(prefix));
}

/**
 * Get config for an indicator by its checkbox ID
 * @param {string} indicatorId - The checkbox ID
 * @param {string} prefix - The prefix used for this chart's IDs
 * @returns {{ key: string, config: Object } | null}
 */
function getIndicatorConfigById(indicatorId, prefix = "") {
  const idToKey = generateIndicatorIdToKey(prefix);
  const key = idToKey[indicatorId];
  if (!key) return null;
  return { key, config: SHARED_INDICATOR_CONFIG[key] };
}

// ============================================================================
// INDICATOR RENDERERS REGISTRY
// Each renderer function takes: (ctx, data, config) and returns series array
// ctx contains: { addLineSeries, getTime, indicatorValues, priceInfo, candleSeries }
// ============================================================================

/**
 * @typedef {Object} IndicatorContext
 * @property {function(Object[], Object, number=): Object} addLineSeries - Add line series
 * @property {function(number): number} getTime - Get time for data index
 * @property {Object} indicatorValues - Storage for indicator tooltip values
 * @property {Object} priceInfo - { minPrice, maxPrice, priceRange, priceMid }
 * @property {Object} candleSeries - The candle series for price lines
 */

const INDICATOR_RENDERERS = {
  ma: (ctx, data, config) => {
    const seriesList = [];
    const maData = calculateMA(data, 20)
      .map((v, i) => ({ time: ctx.getTime(i), value: v }))
      .filter((d) => d.value !== null);
    const series = ctx.addLineSeries(maData, { color: config.color });
    seriesList.push(series);
    maData.forEach((d) => {
      if (!ctx.indicatorValues[d.time]) ctx.indicatorValues[d.time] = {};
      ctx.indicatorValues[d.time].ma = d.value;
    });
    return seriesList;
  },

  ema: (ctx, data, config) => {
    const seriesList = [];
    const emaData = calculateEMA(data, 9)
      .map((v, i) => ({ time: ctx.getTime(i), value: v }))
      .filter((d) => d.value !== null);
    const series = ctx.addLineSeries(emaData, { color: config.color });
    seriesList.push(series);
    emaData.forEach((d) => {
      if (!ctx.indicatorValues[d.time]) ctx.indicatorValues[d.time] = {};
      ctx.indicatorValues[d.time].ema = d.value;
    });
    return seriesList;
  },

  wma: (ctx, data, config) => {
    const seriesList = [];
    const wmaData = calculateWMA(data, 20)
      .map((v, i) => ({ time: ctx.getTime(i), value: v }))
      .filter((d) => d.value !== null);
    const series = ctx.addLineSeries(wmaData, { color: config.color });
    seriesList.push(series);
    wmaData.forEach((d) => {
      if (!ctx.indicatorValues[d.time]) ctx.indicatorValues[d.time] = {};
      ctx.indicatorValues[d.time].wma = d.value;
    });
    return seriesList;
  },

  vwap: (ctx, data, config) => {
    const seriesList = [];
    const vwapData = calculateVWAP(data)
      .map((v, i) => ({ time: ctx.getTime(i), value: v }))
      .filter((d) => d.value !== null);
    const series = ctx.addLineSeries(vwapData, { color: config.color });
    seriesList.push(series);
    vwapData.forEach((d) => {
      if (!ctx.indicatorValues[d.time]) ctx.indicatorValues[d.time] = {};
      ctx.indicatorValues[d.time].vwap = d.value;
    });
    return seriesList;
  },

  bb: (ctx, data, config) => {
    const seriesList = [];
    const bb = calculateBB(data, 20, 2);
    const upperData = bb
      .map((v, i) => ({ time: ctx.getTime(i), value: v.upper }))
      .filter((d) => d.value !== null);
    const lowerData = bb
      .map((v, i) => ({ time: ctx.getTime(i), value: v.lower }))
      .filter((d) => d.value !== null);

    const upperSeries = ctx.addLineSeries(upperData, {
      color: config.color,
      lineStyle: LightweightCharts.LineStyle.Dashed,
    });
    const lowerSeries = ctx.addLineSeries(lowerData, {
      color: config.color,
      lineStyle: LightweightCharts.LineStyle.Dashed,
    });
    seriesList.push(upperSeries, lowerSeries);
    bb.forEach((v, i) => {
      if (v.upper !== null) {
        const time = ctx.getTime(i);
        if (!ctx.indicatorValues[time]) ctx.indicatorValues[time] = {};
        ctx.indicatorValues[time].bbUpper = v.upper;
        ctx.indicatorValues[time].bbMiddle = v.middle;
        ctx.indicatorValues[time].bbLower = v.lower;
      }
    });
    return seriesList;
  },

  atr: (ctx, data, config) => {
    const seriesList = [];
    const { minPrice, priceRange } = ctx.priceInfo;
    const atr = calculateATR(data, 14);
    const atrMax = Math.max(...atr.filter((v) => v !== null)) || 1;
    const atrData = atr
      .map((v, i) => ({
        time: ctx.getTime(i),
        value: v === null ? null : minPrice + (v / atrMax) * priceRange * 0.3,
      }))
      .filter((d) => d.value !== null);
    const series = ctx.addLineSeries(atrData, {
      color: config.color,
      lineStyle: LightweightCharts.LineStyle.Dotted,
    });
    seriesList.push(series);
    atr.forEach((v, i) => {
      if (v !== null) {
        const time = ctx.getTime(i);
        if (!ctx.indicatorValues[time]) ctx.indicatorValues[time] = {};
        ctx.indicatorValues[time].atr = v;
      }
    });
    return seriesList;
  },

  rsi: (ctx, data, config) => {
    const seriesList = [];
    const { minPrice, priceRange } = ctx.priceInfo;
    const rsi = calculateRSI(data, 14);
    const rsiData = rsi
      .map((v, i) => ({
        time: ctx.getTime(i),
        value: v === null ? null : minPrice + (v / 100) * priceRange,
      }))
      .filter((d) => d.value !== null);
    const series = ctx.addLineSeries(rsiData, {
      color: config.color,
      lineStyle: LightweightCharts.LineStyle.Dotted,
    });
    seriesList.push(series);
    rsi.forEach((v, i) => {
      if (v !== null) {
        const time = ctx.getTime(i);
        if (!ctx.indicatorValues[time]) ctx.indicatorValues[time] = {};
        ctx.indicatorValues[time].rsi = v;
      }
    });
    return seriesList;
  },

  macd: (ctx, data, config) => {
    const seriesList = [];
    const { priceMid, priceRange } = ctx.priceInfo;
    const macd = calculateMACD(data, 12, 26, 9);
    const macdValues = macd.macdLine.filter((v) => v !== null);
    const macdMax = Math.max(...macdValues.map(Math.abs)) || 1;
    const scaleMACD = (v) =>
      v === null ? null : priceMid + (v / macdMax) * (priceRange / 4);

    const macdData = macd.macdLine
      .map((v, i) => ({ time: ctx.getTime(i), value: scaleMACD(v) }))
      .filter((d) => d.value !== null);
    const signalData = macd.signalLine
      .map((v, i) => ({ time: ctx.getTime(i), value: scaleMACD(v) }))
      .filter((d) => d.value !== null);

    const macdSeries = ctx.addLineSeries(macdData, {
      color: config.colors.line,
      lineStyle: LightweightCharts.LineStyle.Solid,
    });
    const signalSeries = ctx.addLineSeries(signalData, {
      color: config.colors.signal,
      lineStyle: LightweightCharts.LineStyle.Dashed,
    });
    seriesList.push(macdSeries, signalSeries);
    macd.macdLine.forEach((v, i) => {
      if (
        v !== null ||
        macd.signalLine[i] !== null ||
        macd.histogram[i] !== null
      ) {
        const time = ctx.getTime(i);
        if (!ctx.indicatorValues[time]) ctx.indicatorValues[time] = {};
        ctx.indicatorValues[time].macdLine = v;
        ctx.indicatorValues[time].macdSignal = macd.signalLine[i];
        ctx.indicatorValues[time].macdHist = macd.histogram[i];
      }
    });
    return seriesList;
  },

  stoch: (ctx, data, config) => {
    const seriesList = [];
    const { minPrice, priceRange } = ctx.priceInfo;
    const stoch = calculateStochastic(data, 14, 3, 3);
    const stochK = stoch.k
      .map((v, i) => ({
        time: ctx.getTime(i),
        value: v === null ? null : minPrice + (v / 100) * priceRange,
      }))
      .filter((d) => d.value !== null);
    const stochD = stoch.d
      .map((v, i) => ({
        time: ctx.getTime(i),
        value: v === null ? null : minPrice + (v / 100) * priceRange,
      }))
      .filter((d) => d.value !== null);

    const kSeries = ctx.addLineSeries(stochK, {
      color: config.colors.k,
      lineStyle: LightweightCharts.LineStyle.Solid,
    });
    const dSeries = ctx.addLineSeries(stochD, {
      color: config.colors.d,
      lineStyle: LightweightCharts.LineStyle.Dashed,
    });
    seriesList.push(kSeries, dSeries);
    stoch.k.forEach((v, i) => {
      if (v !== null || stoch.d[i] !== null) {
        const time = ctx.getTime(i);
        if (!ctx.indicatorValues[time]) ctx.indicatorValues[time] = {};
        ctx.indicatorValues[time].stochK = v;
        ctx.indicatorValues[time].stochD = stoch.d[i];
      }
    });
    return seriesList;
  },

  williams: (ctx, data, config) => {
    const seriesList = [];
    const { minPrice, priceRange } = ctx.priceInfo;
    const willR = calculateWilliamsR(data, 14);
    const willRData = willR
      .map((v, i) => ({
        time: ctx.getTime(i),
        value: v === null ? null : minPrice + ((v + 100) / 100) * priceRange,
      }))
      .filter((d) => d.value !== null);
    const series = ctx.addLineSeries(willRData, {
      color: config.color,
      lineStyle: LightweightCharts.LineStyle.Dotted,
    });
    seriesList.push(series);
    willR.forEach((v, i) => {
      if (v !== null) {
        const time = ctx.getTime(i);
        if (!ctx.indicatorValues[time]) ctx.indicatorValues[time] = {};
        ctx.indicatorValues[time].williamsR = v;
      }
    });
    return seriesList;
  },

  cci: (ctx, data, config) => {
    const seriesList = [];
    const { priceMid, priceRange } = ctx.priceInfo;
    const cci = calculateCCI(data, 20);
    const cciMax =
      Math.max(...cci.filter((v) => v !== null).map(Math.abs)) || 100;
    const cciData = cci
      .map((v, i) => ({
        time: ctx.getTime(i),
        value: v === null ? null : priceMid + (v / cciMax) * (priceRange / 4),
      }))
      .filter((d) => d.value !== null);
    const series = ctx.addLineSeries(cciData, {
      color: config.color,
      lineStyle: LightweightCharts.LineStyle.Dotted,
    });
    seriesList.push(series);
    cci.forEach((v, i) => {
      if (v !== null) {
        const time = ctx.getTime(i);
        if (!ctx.indicatorValues[time]) ctx.indicatorValues[time] = {};
        ctx.indicatorValues[time].cci = v;
      }
    });
    return seriesList;
  },

  roc: (ctx, data, config) => {
    const seriesList = [];
    const { priceMid, priceRange } = ctx.priceInfo;
    const roc = calculateROC(data, 10);
    const rocMax =
      Math.max(...roc.filter((v) => v !== null).map(Math.abs)) || 10;
    const rocData = roc
      .map((v, i) => ({
        time: ctx.getTime(i),
        value: v === null ? null : priceMid + (v / rocMax) * (priceRange / 4),
      }))
      .filter((d) => d.value !== null);
    const series = ctx.addLineSeries(rocData, {
      color: config.color,
      lineStyle: LightweightCharts.LineStyle.Dotted,
    });
    seriesList.push(series);
    roc.forEach((v, i) => {
      if (v !== null) {
        const time = ctx.getTime(i);
        if (!ctx.indicatorValues[time]) ctx.indicatorValues[time] = {};
        ctx.indicatorValues[time].roc = v;
      }
    });
    return seriesList;
  },

  adx: (ctx, data, config) => {
    const seriesList = [];
    const { minPrice, priceRange } = ctx.priceInfo;
    const adxResult = calculateADX(data, 14);
    const adxMax = Math.max(...adxResult.adx.filter((v) => v !== null)) || 50;
    const scaleADX = (v) =>
      v === null ? null : minPrice + (v / adxMax) * priceRange * 0.5;

    const adxData = adxResult.adx
      .map((v, i) => ({ time: ctx.getTime(i), value: scaleADX(v) }))
      .filter((d) => d.value !== null);
    const plusDIData = adxResult.plusDI
      .map((v, i) => ({ time: ctx.getTime(i), value: scaleADX(v) }))
      .filter((d) => d.value !== null);
    const minusDIData = adxResult.minusDI
      .map((v, i) => ({ time: ctx.getTime(i), value: scaleADX(v) }))
      .filter((d) => d.value !== null);

    const adxSeries = ctx.addLineSeries(adxData, {
      color: config.colors.adx,
      lineWidth: 2,
      lineStyle: LightweightCharts.LineStyle.Solid,
    });
    const plusDISeries = ctx.addLineSeries(plusDIData, {
      color: config.colors.plusDI,
      lineStyle: LightweightCharts.LineStyle.Dashed,
    });
    const minusDISeries = ctx.addLineSeries(minusDIData, {
      color: config.colors.minusDI,
      lineStyle: LightweightCharts.LineStyle.Dashed,
    });
    seriesList.push(adxSeries, plusDISeries, minusDISeries);
    adxResult.adx.forEach((v, i) => {
      if (v !== null) {
        const time = ctx.getTime(i);
        if (!ctx.indicatorValues[time]) ctx.indicatorValues[time] = {};
        ctx.indicatorValues[time].adx = v;
        ctx.indicatorValues[time].plusDI = adxResult.plusDI[i];
        ctx.indicatorValues[time].minusDI = adxResult.minusDI[i];
      }
    });
    return seriesList;
  },

  volSma: (ctx, data, config) => {
    const seriesList = [];
    const volSmaData = calculateVolumeSMA(data, 20)
      .map((v, i) => ({ time: ctx.getTime(i), value: v }))
      .filter((d) => d.value !== null);
    const series = ctx.addLineSeries(
      volSmaData,
      { color: config.color, lineStyle: LightweightCharts.LineStyle.Solid },
      1,
    );
    seriesList.push(series);
    volSmaData.forEach((d) => {
      if (!ctx.indicatorValues[d.time]) ctx.indicatorValues[d.time] = {};
      ctx.indicatorValues[d.time].volSma = d.value;
    });
    return seriesList;
  },

  obv: (ctx, data, config) => {
    const seriesList = [];
    const obv = calculateOBV(data);
    const obvMax = Math.max(...obv.map(Math.abs)) || 1;
    const volMax = Math.max(...data.map((d) => d.v)) || 1;
    const obvData = obv
      .map((v, i) => ({
        time: ctx.getTime(i),
        value: (v / obvMax) * volMax * 0.8,
      }))
      .filter((d) => d.value !== null);
    const series = ctx.addLineSeries(
      obvData,
      { color: config.color, lineStyle: LightweightCharts.LineStyle.Solid },
      1,
    );
    seriesList.push(series);
    obv.forEach((v, i) => {
      const time = ctx.getTime(i);
      if (!ctx.indicatorValues[time]) ctx.indicatorValues[time] = {};
      ctx.indicatorValues[time].obv = v;
    });
    return seriesList;
  },

  mfi: (ctx, data, config) => {
    const seriesList = [];
    const mfi = calculateMFI(data, 14);
    const volMax = Math.max(...data.map((d) => d.v)) || 1;
    const mfiData = mfi
      .map((v, i) => ({
        time: ctx.getTime(i),
        value: v === null ? null : (v / 100) * volMax * 0.8,
      }))
      .filter((d) => d.value !== null);
    const series = ctx.addLineSeries(
      mfiData,
      { color: config.color, lineStyle: LightweightCharts.LineStyle.Dotted },
      1,
    );
    seriesList.push(series);
    mfi.forEach((v, i) => {
      if (v !== null) {
        const time = ctx.getTime(i);
        if (!ctx.indicatorValues[time]) ctx.indicatorValues[time] = {};
        ctx.indicatorValues[time].mfi = v;
      }
    });
    return seriesList;
  },

  cmf: (ctx, data, config) => {
    const seriesList = [];
    const cmf = calculateCMF(data, 20);
    const volMax = Math.max(...data.map((d) => d.v)) || 1;
    const cmfData = cmf
      .map((v, i) => ({
        time: ctx.getTime(i),
        value: v === null ? null : (v + 1) * 0.5 * volMax * 0.8,
      }))
      .filter((d) => d.value !== null);
    const series = ctx.addLineSeries(
      cmfData,
      { color: config.color, lineStyle: LightweightCharts.LineStyle.Dotted },
      1,
    );
    seriesList.push(series);
    cmf.forEach((v, i) => {
      if (v !== null) {
        const time = ctx.getTime(i);
        if (!ctx.indicatorValues[time]) ctx.indicatorValues[time] = {};
        ctx.indicatorValues[time].cmf = v;
      }
    });
    return seriesList;
  },

  // Pivot and Fib are special - they use price lines, not series
  // These return { type: "priceLines", lines: [...] } instead of series array
  pivot: (ctx, data, config, pivotData = null) => {
    const pp = pivotData || calculatePivotPoints(data[data.length - 1]);
    const colors = config.colors;
    const priceLines = [];
    const addPivotLine = (price, color, title) => {
      if (price && typeof price === "number" && !isNaN(price)) {
        const priceLine = ctx.candleSeries.createPriceLine({
          price: price,
          color: color,
          lineWidth: 1,
          lineStyle: LightweightCharts.LineStyle.Dashed,
          axisLabelVisible: true,
          title: title,
        });
        priceLines.push(priceLine);
      }
    };
    addPivotLine(pp.pivot, colors.pivot, "P");
    addPivotLine(pp.r1, colors.resistance, "R1");
    addPivotLine(pp.r2, colors.resistance, "R2");
    addPivotLine(pp.r3, colors.resistance, "R3");
    addPivotLine(pp.s1, colors.support, "S1");
    addPivotLine(pp.s2, colors.support, "S2");
    addPivotLine(pp.s3, colors.support, "S3");
    return { type: "priceLines", lines: priceLines };
  },

  fib: (ctx, data, config, fibData = null) => {
    const fib = fibData || calculateFibonacciLevels(data, 50);
    const colors = config.colors;
    const priceLines = [];
    const addFibLine = (price, color, title) => {
      if (price && typeof price === "number" && !isNaN(price)) {
        const priceLine = ctx.candleSeries.createPriceLine({
          price: price,
          color: color,
          lineWidth: 1,
          lineStyle: LightweightCharts.LineStyle.Dotted,
          axisLabelVisible: true,
          title: title,
        });
        priceLines.push(priceLine);
      }
    };
    addFibLine(fib.level_0, colors.key, "0%");
    addFibLine(fib.level_236, colors.level, "23.6%");
    addFibLine(fib.level_382, colors.key, "38.2%");
    addFibLine(fib.level_500, colors.key, "50%");
    addFibLine(fib.level_618, colors.key, "61.8%");
    addFibLine(fib.level_786, colors.level, "78.6%");
    addFibLine(fib.level_100, colors.key, "100%");
    return { type: "priceLines", lines: priceLines };
  },
};

/**
 * Render an indicator using the shared registry
 * @param {string} indicatorKey - The config key (e.g., "ma", "rsi")
 * @param {IndicatorContext} ctx - Context object with chart-specific functions
 * @param {Array} data - OHLCV data array
 * @param {Object} config - Indicator config from SHARED_INDICATOR_CONFIG
 * @param {Object} [extraData] - Optional extra data (pivot/fib data from analysis)
 * @returns {Object[]|{type: string, lines: Object[]}|null}
 */
function renderIndicator(indicatorKey, ctx, data, config, extraData = null) {
  const renderer = INDICATOR_RENDERERS[indicatorKey];
  if (!renderer) return null;

  // For pivot/fib, pass extra data if available
  if ((indicatorKey === "pivot" || indicatorKey === "fib") && extraData) {
    return renderer(ctx, data, config, extraData);
  }
  return renderer(ctx, data, config);
}

/**
 * Create a tooltip element for chart
 * @param {HTMLElement} targetContainer - Container to append tooltip to
 * @returns {HTMLDivElement} - Tooltip element
 */
function createChartTooltip(targetContainer) {
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
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    backdrop-filter: blur(8px);
  `;
  targetContainer.style.position = "relative";
  targetContainer.appendChild(tooltip);
  return tooltip;
}

/**
 * Apply theme styles to tooltip
 * @param {HTMLDivElement} tooltip - Tooltip element
 */
function applyTooltipTheme(tooltip) {
  const isDark = document.documentElement.classList.contains("dark");
  if (isDark) {
    tooltip.style.background = "rgba(30, 41, 59, 0.95)";
    tooltip.style.color = "#e2e8f0";
    tooltip.style.border = "1px solid rgba(148, 163, 184, 0.2)";
  } else {
    tooltip.style.background = "rgba(255, 255, 255, 0.95)";
    tooltip.style.color = "#1e293b";
    tooltip.style.border = "1px solid rgba(100, 116, 139, 0.2)";
  }
}

/**
 * Update tooltip position to follow crosshair
 * @param {HTMLDivElement} tooltip - Tooltip element
 * @param {HTMLElement} container - Container element
 * @param {Object} param - Crosshair param with point
 */
function updateTooltipPosition(tooltip, container, param) {
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
}

/**
 * Render indicator values for price chart tooltip
 * @param {Object} indicatorValues - Object mapping time -> indicator values
 * @param {number | string} time - Unix timestamp
 * @param {Object} config - Indicator config to use (INDICATOR_CONFIG or ANALYSIS_INDICATOR_CONFIG)
 * @returns {string} - HTML string for indicator values
 */
function renderPriceIndicatorsTooltip(indicatorValues, time, config) {
  const values = indicatorValues[time];
  if (!values) return "";

  let html =
    '<div style="margin-top: 6px; border-top: 1px solid rgba(148, 163, 184, 0.2); padding-top: 4px;">';
  let count = 0;

  // Moving Averages
  if (values.ma !== undefined) {
    html += `<div><span style="color: ${
      config.ma?.color || SHARED_INDICATOR_CONFIG.ma.color
    }; opacity: 0.8;">SMA(20):</span> <strong>${formatPrice(
      values.ma,
    )}</strong></div>`;
    count++;
  }
  if (values.ema !== undefined) {
    html += `<div><span style="color: ${
      config.ema?.color || SHARED_INDICATOR_CONFIG.ema.color
    }; opacity: 0.8;">EMA(9):</span> <strong>${formatPrice(
      values.ema,
    )}</strong></div>`;
    count++;
  }
  if (values.wma !== undefined) {
    html += `<div><span style="color: ${
      config.wma?.color || SHARED_INDICATOR_CONFIG.wma.color
    }; opacity: 0.8;">WMA(20):</span> <strong>${formatPrice(
      values.wma,
    )}</strong></div>`;
    count++;
  }
  if (values.vwap !== undefined) {
    html += `<div><span style="color: ${
      config.vwap?.color || SHARED_INDICATOR_CONFIG.vwap.color
    }; opacity: 0.8;">VWAP:</span> <strong>${formatPrice(
      values.vwap,
    )}</strong></div>`;
    count++;
  }

  // Bands
  if (values.bbUpper !== undefined) {
    html += `<div><span style="color: ${
      config.bb?.color || SHARED_INDICATOR_CONFIG.bb.color
    }; opacity: 0.8;">BB Upper:</span> <strong>${formatPrice(
      values.bbUpper,
    )}</strong></div>`;
    html += `<div><span style="color: ${
      config.bb?.color || SHARED_INDICATOR_CONFIG.bb.color
    }; opacity: 0.8;">BB Lower:</span> <strong>${formatPrice(
      values.bbLower,
    )}</strong></div>`;
    count++;
  }
  if (values.atr !== undefined) {
    html += `<div><span style="color: ${
      config.atr?.color || SHARED_INDICATOR_CONFIG.atr.color
    }; opacity: 0.8;">ATR(14):</span> <strong>${formatNumber(
      values.atr,
      2,
    )}</strong></div>`;
    count++;
  }

  // Oscillators
  if (values.rsi !== undefined) {
    html += `<div><span style="color: ${
      config.rsi?.color || SHARED_INDICATOR_CONFIG.rsi.color
    }; opacity: 0.8;">RSI(14):</span> <strong>${formatNumber(
      values.rsi,
      2,
    )}</strong></div>`;
    count++;
  }
  if (values.macdLine !== undefined) {
    const macdColors =
      config.macd?.colors || SHARED_INDICATOR_CONFIG.macd.colors;
    html += `<div><span style="color: ${
      macdColors.line
    }; opacity: 0.8;">MACD:</span> <strong>${formatNumber(
      values.macdLine,
      2,
    )}</strong></div>`;
    html += `<div><span style="color: ${
      macdColors.signal
    }; opacity: 0.8;">Signal:</span> <strong>${formatNumber(
      values.macdSignal,
      2,
    )}</strong></div>`;
    count++;
  }
  if (values.stochK !== undefined) {
    const stochColors =
      config.stoch?.colors || SHARED_INDICATOR_CONFIG.stoch.colors;
    html += `<div><span style="color: ${
      stochColors.k
    }; opacity: 0.8;">Stoch %K:</span> <strong>${formatNumber(
      values.stochK,
      2,
    )}</strong></div>`;
    html += `<div><span style="color: ${
      stochColors.d
    }; opacity: 0.8;">Stoch %D:</span> <strong>${formatNumber(
      values.stochD,
      2,
    )}</strong></div>`;
    count++;
  }
  // Williams %R - check both possible key names
  if (values.williamsR !== undefined || values.williams !== undefined) {
    const willVal =
      values.williamsR !== undefined ? values.williamsR : values.williams;
    html += `<div><span style="color: ${
      config.williams?.color || SHARED_INDICATOR_CONFIG.williams.color
    }; opacity: 0.8;">Will %R:</span> <strong>${formatNumber(
      willVal,
      2,
    )}</strong></div>`;
    count++;
  }
  if (values.cci !== undefined) {
    html += `<div><span style="color: ${
      config.cci?.color || SHARED_INDICATOR_CONFIG.cci.color
    }; opacity: 0.8;">CCI(20):</span> <strong>${formatNumber(
      values.cci,
      2,
    )}</strong></div>`;
    count++;
  }
  if (values.roc !== undefined) {
    html += `<div><span style="color: ${
      config.roc?.color || SHARED_INDICATOR_CONFIG.roc.color
    }; opacity: 0.8;">ROC(10):</span> <strong>${formatNumber(
      values.roc,
      2,
    )}%</strong></div>`;
    count++;
  }

  // Trend
  if (values.adx !== undefined) {
    const adxColors = config.adx?.colors || SHARED_INDICATOR_CONFIG.adx.colors;
    html += `<div><span style="color: ${
      adxColors.adx
    }; opacity: 0.8;">ADX:</span> <strong>${formatNumber(
      values.adx,
      2,
    )}</strong></div>`;
    html += `<div><span style="color: ${
      adxColors.plusDI
    }; opacity: 0.8;">+DI:</span> <strong>${formatNumber(
      values.plusDI,
      2,
    )}</strong></div>`;
    html += `<div><span style="color: ${
      adxColors.minusDI
    }; opacity: 0.8;">-DI:</span> <strong>${formatNumber(
      values.minusDI,
      2,
    )}</strong></div>`;
    count++;
  }

  html += "</div>";
  return count > 0 ? html : "";
}

/**
 * Render volume indicator values for tooltip
 * @param {Object} indicatorValues - Object mapping time -> indicator values
 * @param {number | string} time - Unix timestamp or date string
 * @param {Object} config - Indicator config to use
 * @returns {string} - HTML string for volume indicator values
 */
function renderVolumeIndicatorsTooltip(indicatorValues, time, config) {
  const values = indicatorValues[time];
  if (!values) return "";

  let html =
    '<div style="margin-top: 6px; border-top: 1px solid rgba(148, 163, 184, 0.2); padding-top: 4px;">';
  let count = 0;

  if (values.volSma !== undefined) {
    html += `<div><span style="color: ${
      config.volSma?.color || SHARED_INDICATOR_CONFIG.volSma.color
    }; opacity: 0.8;">Vol SMA(20):</span> <strong>${formatNumber(
      values.volSma,
      0,
    )}</strong></div>`;
    count++;
  }
  if (values.obv !== undefined) {
    html += `<div><span style="color: ${
      config.obv?.color || SHARED_INDICATOR_CONFIG.obv.color
    }; opacity: 0.8;">OBV:</span> <strong>${formatNumber(
      values.obv,
      0,
    )}</strong></div>`;
    count++;
  }
  if (values.mfi !== undefined) {
    html += `<div><span style="color: ${
      config.mfi?.color || SHARED_INDICATOR_CONFIG.mfi.color
    }; opacity: 0.8;">MFI(14):</span> <strong>${formatNumber(
      values.mfi,
      2,
    )}</strong></div>`;
    count++;
  }
  if (values.cmf !== undefined) {
    html += `<div><span style="color: ${
      config.cmf?.color || SHARED_INDICATOR_CONFIG.cmf.color
    }; opacity: 0.8;">CMF(20):</span> <strong>${formatNumber(
      values.cmf,
      4,
    )}</strong></div>`;
    count++;
  }

  html += "</div>";
  return count > 0 ? html : "";
}

/**
 * Render all indicator values for tooltip (both price and volume)
 * @param {Object} indicatorValues - Object mapping time -> indicator values
 * @param {number | string} time - Unix timestamp
 * @param {Object} config - Indicator config to use
 * @param {boolean} isVolumeChart - Whether this is for volume chart only
 * @returns {string} - HTML string for indicator values
 */
function renderTooltipIndicators(
  indicatorValues,
  time,
  config,
  isVolumeChart = false,
) {
  if (isVolumeChart) {
    return renderVolumeIndicatorsTooltip(indicatorValues, time, config);
  }
  return renderPriceIndicatorsTooltip(indicatorValues, time, config);
}
